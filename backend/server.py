from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import json
from bson import ObjectId

# Custom JSON encoder to handle MongoDB ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

# Import our scraper modules
from backend.scraper.real_dealer_scraper import RealDealerScraper as AdvancedCarScraper
from backend.scraper.models import Vehicle, ScrapingJob

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize the scraper
scraper = AdvancedCarScraper()

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class ScrapingRequest(BaseModel):
    dealer_urls: List[str]
    max_vehicles_per_dealer: Optional[int] = 100

class ScrapingResponse(BaseModel):
    job_id: str
    status: str
    message: str

# Existing routes
@api_router.get("/")
async def root():
    return {"message": "Pulse Auto Market - Advanced Car Scraper API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# New Scraping Routes
@api_router.post("/scrape/start", response_model=ScrapingResponse)
async def start_scraping(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """Start scraping multiple dealer websites"""
    job_id = str(uuid.uuid4())
    
    # Create scraping job record
    job = ScrapingJob(
        id=job_id,
        dealer_urls=request.dealer_urls,
        status="starting",
        max_vehicles_per_dealer=request.max_vehicles_per_dealer,
        created_at=datetime.utcnow()
    )
    
    await db.scraping_jobs.insert_one(job.dict())
    
    # Start background scraping task
    background_tasks.add_task(run_scraping_job, job_id, request.dealer_urls, request.max_vehicles_per_dealer)
    
    return ScrapingResponse(
        job_id=job_id,
        status="started",
        message=f"Scraping job started for {len(request.dealer_urls)} dealers"
    )

@api_router.get("/scrape/status/{job_id}")
async def get_scraping_status(job_id: str):
    """Get status of a scraping job"""
    job = await db.scraping_jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get vehicle count for this job
    vehicle_count = await db.vehicles.count_documents({"scraping_job_id": job_id})
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0),
        "vehicles_scraped": vehicle_count,
        "dealers_completed": job.get("dealers_completed", 0),
        "total_dealers": len(job["dealer_urls"]),
        "created_at": job["created_at"],
        "updated_at": job.get("updated_at"),
        "error_message": job.get("error_message")
    }

@api_router.get("/scrape/jobs")
async def get_scraping_jobs():
    """Get all scraping jobs"""
    jobs = await db.scraping_jobs.find().sort("created_at", -1).to_list(50)
    # Convert ObjectId to string
    for job in jobs:
        if "_id" in job:
            job["_id"] = str(job["_id"])
    return jobs

@api_router.get("/vehicles")
async def get_vehicles(limit: int = 50, skip: int = 0, dealer_url: Optional[str] = None):
    """Get scraped vehicles with optional filtering"""
    query = {}
    if dealer_url:
        query["dealer_url"] = dealer_url
    
    vehicles = await db.vehicles.find(query).sort("scraped_at", -1).skip(skip).limit(limit).to_list(limit)
    total_count = await db.vehicles.count_documents(query)
    
    # Convert ObjectId to string
    for vehicle in vehicles:
        if "_id" in vehicle:
            vehicle["_id"] = str(vehicle["_id"])
    
    return {
        "vehicles": vehicles,
        "total": total_count,
        "limit": limit,
        "skip": skip
    }

@api_router.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str):
    """Get single vehicle by ID"""
    vehicle = await db.vehicles.find_one({"id": vehicle_id})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Convert ObjectId to string
    if "_id" in vehicle:
        vehicle["_id"] = str(vehicle["_id"])
    
    return vehicle

@api_router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: str):
    """Delete a vehicle"""
    result = await db.vehicles.delete_one({"id": vehicle_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return {"message": "Vehicle deleted successfully"}

@api_router.get("/dealers/stats")
async def get_dealer_stats():
    """Get statistics about scraped dealers"""
    pipeline = [
        {"$group": {
            "_id": "$dealer_url",
            "vehicle_count": {"$sum": 1},
            "last_scraped": {"$max": "$scraped_at"},
            "dealer_name": {"$first": "$dealer_name"}
        }},
        {"$sort": {"vehicle_count": -1}}
    ]
    
    stats = await db.vehicles.aggregate(pipeline).to_list(100)
    
    # Convert ObjectId to string
    for stat in stats:
        if "_id" in stat:
            stat["_id"] = str(stat["_id"])
    
    return stats

# Background task function
async def run_scraping_job(job_id: str, dealer_urls: List[str], max_vehicles_per_dealer: int):
    """Background task to run the scraping job"""
    try:
        # Update job status
        await db.scraping_jobs.update_one(
            {"id": job_id},
            {"$set": {"status": "running", "updated_at": datetime.utcnow()}}
        )
        
        total_dealers = len(dealer_urls)
        dealers_completed = 0
        total_vehicles_scraped = 0
        
        for dealer_url in dealer_urls:
            try:
                logger.info(f"Starting to scrape dealer: {dealer_url}")
                
                # Scrape this dealer
                vehicles = await scraper.scrape_dealer(dealer_url, max_vehicles_per_dealer)
                
                # Save vehicles to database
                for vehicle in vehicles:
                    vehicle_dict = vehicle.dict()
                    vehicle_dict["scraping_job_id"] = job_id
                    await db.vehicles.insert_one(vehicle_dict)
                
                dealers_completed += 1
                total_vehicles_scraped += len(vehicles)
                
                # Update progress
                progress = int((dealers_completed / total_dealers) * 100)
                await db.scraping_jobs.update_one(
                    {"id": job_id},
                    {"$set": {
                        "progress": progress,
                        "dealers_completed": dealers_completed,
                        "updated_at": datetime.utcnow()
                    }}
                )
                
                logger.info(f"Completed scraping {dealer_url}: {len(vehicles)} vehicles")
                
                # Add delay between dealers to be respectful
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error scraping dealer {dealer_url}: {str(e)}")
                continue
        
        # Mark job as completed
        await db.scraping_jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "completed",
                "progress": 100,
                "dealers_completed": dealers_completed,
                "total_vehicles_scraped": total_vehicles_scraped,
                "updated_at": datetime.utcnow()
            }}
        )
        
        logger.info(f"Scraping job {job_id} completed: {total_vehicles_scraped} vehicles from {dealers_completed} dealers")
        
    except Exception as e:
        logger.error(f"Scraping job {job_id} failed: {str(e)}")
        await db.scraping_jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "failed",
                "error_message": str(e),
                "updated_at": datetime.utcnow()
            }}
        )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()