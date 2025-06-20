from fastapi import FastAPI, APIRouter, HTTPException, Query, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import httpx
import asyncio
from bs4 import BeautifulSoup
import re
import json

# Import our enhanced services
from image_service import VehicleImageManager
from ai_crm_service import AICRMService, Lead, LeadStatus, LeadScore, InquiryType, ConversationMessage
from desking_service import DeskingService, DealCalculation, DealType, PaymentGrid, FIProduct, TradeIn, TaxInfo, FinanceTerms, LeaseTerms

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize services
image_manager = VehicleImageManager(db)
ai_crm_service = AICRMService(db)
desking_service = DeskingService(db)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Vehicle Models (Enhanced with better image support)
class Vehicle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vin: str
    make: str
    model: str
    year: int
    mileage: int
    price: float
    dealer_name: str
    dealer_location: str
    exterior_color: Optional[str] = None
    interior_color: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    drivetrain: Optional[str] = None
    engine: Optional[str] = None
    images: List[str] = []  # Thumbnail URLs for quick display
    image_count: int = 0    # Total number of images available
    deal_pulse_rating: Optional[str] = None  # "Great Deal", "Fair Price", "High Price"
    market_price_analysis: Optional[dict] = None
    scraped_from_url: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class VehicleCreate(BaseModel):
    vin: str
    make: str
    model: str
    year: int
    mileage: int
    price: float
    dealer_name: str
    dealer_location: str
    exterior_color: Optional[str] = None
    interior_color: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    drivetrain: Optional[str] = None
    engine: Optional[str] = None
    images: List[str] = []
    scraped_from_url: Optional[str] = None

class VehicleImageResponse(BaseModel):
    vin: str
    images: List[dict]
    total_count: int
    scraped_at: Optional[datetime] = None

# Dealer Models
class Dealer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    website_url: str
    location: str
    scraper_adapter: str  # "generic", "carmax", "cargurus", etc.
    last_scraped: Optional[datetime] = None
    vehicle_count: int = 0
    image_scraping_enabled: bool = True
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DealerCreate(BaseModel):
    name: str
    website_url: str
    location: str
    scraper_adapter: str = "generic"
    image_scraping_enabled: bool = True

# Scraping Job Models
class ScrapeJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dealer_id: str
    status: str  # "pending", "running", "completed", "failed"
    vehicles_found: int = 0
    vehicles_added: int = 0
    images_scraped: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# VIN Decoding Service
async def decode_vin(vin: str) -> dict:
    """Decode VIN using NHTSA API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
            )
            if response.status_code == 200:
                data = response.json()
                results = data.get('Results', [])
                
                # Extract key information
                decoded_info = {}
                for result in results:
                    variable = result.get('Variable', '')
                    value = result.get('Value', '')
                    
                    if variable == 'Make' and value:
                        decoded_info['make'] = value
                    elif variable == 'Model' and value:
                        decoded_info['model'] = value
                    elif variable == 'Model Year' and value:
                        try:
                            decoded_info['year'] = int(value)
                        except:
                            pass
                    elif variable == 'Fuel Type - Primary' and value:
                        decoded_info['fuel_type'] = value
                    elif variable == 'Transmission Style' and value:
                        decoded_info['transmission'] = value
                    elif variable == 'Drive Type' and value:
                        decoded_info['drivetrain'] = value
                    elif variable == 'Engine Configuration' and value:
                        decoded_info['engine'] = value
                
                return decoded_info
    except Exception as e:
        logging.error(f"VIN decoding failed for {vin}: {str(e)}")
        return {}

# Deal Pulse Analysis
def calculate_deal_pulse(vehicle_data: dict, market_data: List[dict]) -> dict:
    """Calculate Deal Pulse rating based on market comparison"""
    try:
        price = vehicle_data.get('price', 0)
        year = vehicle_data.get('year', 2020)
        mileage = vehicle_data.get('mileage', 50000)
        
        # Simple market analysis (in real implementation, this would use ML)
        similar_vehicles = [v for v in market_data if 
                          v.get('make') == vehicle_data.get('make') and
                          v.get('model') == vehicle_data.get('model') and
                          abs(v.get('year', 2020) - year) <= 2]
        
        if not similar_vehicles:
            return {
                "rating": "Unknown",
                "confidence": "Low",
                "market_average": None,
                "savings": None
            }
        
        # Calculate market average
        market_prices = [v.get('price', 0) for v in similar_vehicles if v.get('price', 0) > 0]
        if not market_prices:
            return {
                "rating": "Unknown",
                "confidence": "Low",
                "market_average": None,
                "savings": None
            }
        
        market_avg = sum(market_prices) / len(market_prices)
        price_diff = market_avg - price
        price_diff_pct = (price_diff / market_avg) * 100
        
        # Determine rating
        if price_diff_pct >= 10:
            rating = "Great Deal"
        elif price_diff_pct >= 0:
            rating = "Fair Price"
        else:
            rating = "High Price"
        
        return {
            "rating": rating,
            "confidence": "Medium" if len(similar_vehicles) >= 3 else "Low",
            "market_average": round(market_avg, 2),
            "savings": round(price_diff, 2) if price_diff > 0 else 0,
            "comparison_count": len(similar_vehicles)
        }
    except Exception as e:
        logging.error(f"Deal Pulse calculation failed: {str(e)}")
        return {
            "rating": "Unknown",
            "confidence": "Low",
            "market_average": None,
            "savings": None
        }

# Enhanced scraper with image support
async def scrape_dealer_inventory(dealer: dict) -> List[dict]:
    """Enhanced web scraper for dealer websites with image support"""
    vehicles = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(dealer['website_url'])
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for common vehicle listing patterns
                vehicle_selectors = [
                    '.vehicle-card', '.car-card', '.inventory-item',
                    '.vehicle-listing', '.car-listing', '[data-vin]'
                ]
                
                vehicle_elements = []
                for selector in vehicle_selectors:
                    elements = soup.select(selector)
                    if elements:
                        vehicle_elements = elements
                        break
                
                for element in vehicle_elements[:20]:  # Limit to 20 vehicles per scrape
                    try:
                        # Extract VIN (various patterns)
                        vin = None
                        vin_patterns = [
                            element.get('data-vin'),
                            element.get('data-vehicle-id'),
                        ]
                        
                        # Look for VIN in text
                        element_text = element.get_text()
                        vin_match = re.search(r'\b[A-HJ-NPR-Z0-9]{17}\b', element_text)
                        if vin_match:
                            vin = vin_match.group()
                        
                        # Look for VIN in various attributes
                        for pattern in vin_patterns:
                            if pattern and len(str(pattern)) == 17:
                                vin = str(pattern)
                                break
                        
                        if not vin:
                            continue
                        
                        # Extract price
                        price_text = element.get_text()
                        price_match = re.search(r'\$[\d,]+', price_text)
                        price = 0
                        if price_match:
                            price_str = price_match.group().replace('$', '').replace(',', '')
                            try:
                                price = float(price_str)
                            except:
                                pass
                        
                        # Extract mileage
                        mileage_match = re.search(r'(\d+,?\d*)\s*(miles|mi)', price_text, re.IGNORECASE)
                        mileage = 0
                        if mileage_match:
                            mileage_str = mileage_match.group(1).replace(',', '')
                            try:
                                mileage = int(mileage_str)
                            except:
                                pass
                        
                        # Get VIN decoded info
                        decoded_info = await decode_vin(vin)
                        
                        # Extract detail page URL for image scraping
                        detail_url = None
                        link_element = element.find('a')
                        if link_element and link_element.get('href'):
                            detail_url = link_element['href']
                            if not detail_url.startswith('http'):
                                from urllib.parse import urljoin
                                detail_url = urljoin(dealer['website_url'], detail_url)
                        
                        vehicle_data = {
                            'vin': vin,
                            'make': decoded_info.get('make', 'Unknown'),
                            'model': decoded_info.get('model', 'Unknown'),
                            'year': decoded_info.get('year', 2020),
                            'mileage': mileage,
                            'price': price,
                            'dealer_name': dealer['name'],
                            'dealer_location': dealer['location'],
                            'fuel_type': decoded_info.get('fuel_type'),
                            'transmission': decoded_info.get('transmission'),
                            'drivetrain': decoded_info.get('drivetrain'),
                            'engine': decoded_info.get('engine'),
                            'images': [],  # Will be populated by image scraper
                            'scraped_from_url': detail_url or dealer['website_url']
                        }
                        
                        if price > 0:  # Only add vehicles with valid price
                            vehicles.append(vehicle_data)
                    
                    except Exception as e:
                        logging.error(f"Error processing vehicle element: {str(e)}")
                        continue
                        
    except Exception as e:
        logging.error(f"Error scraping dealer {dealer['name']}: {str(e)}")
    
    return vehicles

# Initialize image manager on startup
@app.on_event("startup")
async def startup_event():
    await image_manager.initialize()
    logging.info("Image manager initialized")

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Pulse Auto Market API - Enhanced with Image Processing"}

# Vehicle Routes
@api_router.post("/vehicles", response_model=Vehicle)
async def create_vehicle(vehicle: VehicleCreate, background_tasks: BackgroundTasks):
    """Create a new vehicle listing with image scraping"""
    vehicle_dict = vehicle.dict()
    vehicle_obj = Vehicle(**vehicle_dict)
    
    # Calculate Deal Pulse rating
    existing_vehicles = await db.vehicles.find().to_list(1000)
    market_analysis = calculate_deal_pulse(vehicle_dict, existing_vehicles)
    vehicle_obj.deal_pulse_rating = market_analysis['rating']
    vehicle_obj.market_price_analysis = market_analysis
    
    # Insert vehicle first
    await db.vehicles.insert_one(vehicle_obj.dict())
    
    # Trigger image scraping in background if URL provided
    if vehicle.scraped_from_url:
        background_tasks.add_task(
            image_manager.scrape_and_store_images,
            vehicle_obj.id,
            vehicle_obj.vin,
            vehicle.scraped_from_url
        )
    
    return vehicle_obj

@api_router.get("/vehicles", response_model=List[Vehicle])
async def get_vehicles(
    limit: int = Query(20, le=100),
    skip: int = Query(0, ge=0),
    make: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    year_min: Optional[int] = Query(None),
    year_max: Optional[int] = Query(None),
    price_min: Optional[float] = Query(None),
    price_max: Optional[float] = Query(None),
    mileage_max: Optional[int] = Query(None),
    location: Optional[str] = Query(None)
):
    """Get vehicles with filtering and pagination"""
    query = {}
    
    if make:
        query['make'] = {"$regex": make, "$options": "i"}
    if model:
        query['model'] = {"$regex": model, "$options": "i"}
    if year_min or year_max:
        year_query = {}
        if year_min:
            year_query['$gte'] = year_min
        if year_max:
            year_query['$lte'] = year_max
        query['year'] = year_query
    if price_min or price_max:
        price_query = {}
        if price_min:
            price_query['$gte'] = price_min
        if price_max:
            price_query['$lte'] = price_max
        query['price'] = price_query
    if mileage_max:
        query['mileage'] = {"$lte": mileage_max}
    if location:
        query['dealer_location'] = {"$regex": location, "$options": "i"}
    
    vehicles = await db.vehicles.find(query).skip(skip).limit(limit).to_list(limit)
    return [Vehicle(**vehicle) for vehicle in vehicles]

@api_router.get("/vehicles/{vin}", response_model=Vehicle)
async def get_vehicle_by_vin(vin: str):
    """Get a specific vehicle by VIN"""
    vehicle = await db.vehicles.find_one({"vin": vin})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return Vehicle(**vehicle)

@api_router.get("/vehicles/{vin}/images", response_model=VehicleImageResponse)
async def get_vehicle_images(vin: str):
    """Get all images for a specific vehicle"""
    images_data = await image_manager.get_vehicle_images(vin)
    return VehicleImageResponse(**images_data)

@api_router.post("/vehicles/{vin}/scrape-images")
async def scrape_vehicle_images(vin: str, background_tasks: BackgroundTasks):
    """Trigger image scraping for a specific vehicle"""
    vehicle = await db.vehicles.find_one({"vin": vin})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    if not vehicle.get('scraped_from_url'):
        raise HTTPException(status_code=400, detail="No source URL available for scraping")
    
    # Trigger image scraping in background
    background_tasks.add_task(
        image_manager.scrape_and_store_images,
        vehicle['id'],
        vin,
        vehicle['scraped_from_url']
    )
    
    return {"message": "Image scraping started", "vin": vin}

@api_router.get("/vehicles/search/makes")
async def get_available_makes():
    """Get all available vehicle makes"""
    makes = await db.vehicles.distinct("make")
    return {"makes": sorted([make for make in makes if make and make != "Unknown"])}

@api_router.get("/vehicles/search/models")
async def get_available_models(make: Optional[str] = Query(None)):
    """Get all available vehicle models, optionally filtered by make"""
    query = {}
    if make:
        query['make'] = {"$regex": make, "$options": "i"}
    
    models = await db.vehicles.distinct("model", query)
    return {"models": sorted([model for model in models if model and model != "Unknown"])}

# Dealer Routes
@api_router.post("/dealers", response_model=Dealer)
async def create_dealer(dealer: DealerCreate):
    """Create a new dealer"""
    dealer_dict = dealer.dict()
    dealer_obj = Dealer(**dealer_dict)
    await db.dealers.insert_one(dealer_obj.dict())
    return dealer_obj

@api_router.get("/dealers", response_model=List[Dealer])
async def get_dealers():
    """Get all dealers"""
    dealers = await db.dealers.find().to_list(1000)
    return [Dealer(**dealer) for dealer in dealers]

# Enhanced Scraping Routes with Image Support
@api_router.post("/scrape/dealer/{dealer_id}")
async def scrape_dealer(dealer_id: str, background_tasks: BackgroundTasks):
    """Trigger scraping for a specific dealer with image support"""
    dealer = await db.dealers.find_one({"id": dealer_id})
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
    
    # Create scrape job
    job = ScrapeJob(dealer_id=dealer_id, status="running", started_at=datetime.utcnow())
    await db.scrape_jobs.insert_one(job.dict())
    
    try:
        # Scrape vehicles
        vehicles = await scrape_dealer_inventory(dealer)
        
        # Save vehicles to database and trigger image scraping
        vehicles_added = 0
        images_scraped = 0
        
        for vehicle_data in vehicles:
            try:
                # Check if vehicle already exists
                existing = await db.vehicles.find_one({"vin": vehicle_data['vin']})
                if existing:
                    # Update existing vehicle
                    await db.vehicles.update_one(
                        {"vin": vehicle_data['vin']},
                        {"$set": {**vehicle_data, "last_updated": datetime.utcnow()}}
                    )
                else:
                    # Create new vehicle
                    vehicle_obj = Vehicle(**vehicle_data)
                    
                    # Calculate Deal Pulse rating
                    existing_vehicles = await db.vehicles.find().to_list(1000)
                    market_analysis = calculate_deal_pulse(vehicle_data, existing_vehicles)
                    vehicle_obj.deal_pulse_rating = market_analysis['rating']
                    vehicle_obj.market_price_analysis = market_analysis
                    
                    await db.vehicles.insert_one(vehicle_obj.dict())
                    vehicles_added += 1
                
                # Trigger image scraping if enabled and URL available
                if (dealer.get('image_scraping_enabled', True) and 
                    vehicle_data.get('scraped_from_url')):
                    background_tasks.add_task(
                        image_manager.scrape_and_store_images,
                        vehicle_data.get('id', str(uuid.uuid4())),
                        vehicle_data['vin'],
                        vehicle_data['scraped_from_url']
                    )
                    images_scraped += 1
                    
            except Exception as e:
                logging.error(f"Error saving vehicle {vehicle_data.get('vin')}: {str(e)}")
        
        # Update dealer stats
        vehicle_count = await db.vehicles.count_documents({"dealer_name": dealer['name']})
        await db.dealers.update_one(
            {"id": dealer_id},
            {"$set": {"last_scraped": datetime.utcnow(), "vehicle_count": vehicle_count}}
        )
        
        # Update job status
        await db.scrape_jobs.update_one(
            {"id": job.id},
            {"$set": {
                "status": "completed",
                "vehicles_found": len(vehicles),
                "vehicles_added": vehicles_added,
                "images_scraped": images_scraped,
                "completed_at": datetime.utcnow()
            }}
        )
        
        return {
            "message": "Scraping completed successfully",
            "vehicles_found": len(vehicles),
            "vehicles_added": vehicles_added,
            "images_scraped": images_scraped,
            "dealer": dealer['name']
        }
        
    except Exception as e:
        await db.scrape_jobs.update_one(
            {"id": job.id},
            {"$set": {
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.utcnow()
            }}
        )
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@api_router.get("/scrape/jobs", response_model=List[ScrapeJob])
async def get_scrape_jobs():
    """Get all scrape jobs"""
    jobs = await db.scrape_jobs.find().sort("created_at", -1).to_list(100)
    return [ScrapeJob(**job) for job in jobs]

# Image Management Routes
@api_router.post("/images/cleanup")
async def cleanup_expired_images():
    """Clean up expired images"""
    cleaned_count = await image_manager.cleanup_expired_images()
    return {
        "message": f"Cleaned up {cleaned_count} expired image records",
        "cleaned_count": cleaned_count
    }

@api_router.get("/images/stats")
async def get_image_stats():
    """Get image storage statistics"""
    try:
        total_image_records = await db.vehicle_images.count_documents({})
        total_vehicles_with_images = await db.vehicles.count_documents({"images": {"$ne": []}})
        
        # Get average images per vehicle
        pipeline = [
            {"$match": {"images": {"$ne": []}}},
            {"$project": {"image_count": {"$size": "$images"}}},
            {"$group": {"_id": None, "avg_images": {"$avg": "$image_count"}}}
        ]
        avg_result = await db.vehicle_images.aggregate(pipeline).to_list(1)
        avg_images = avg_result[0]['avg_images'] if avg_result else 0
        
        return {
            "total_image_records": total_image_records,
            "vehicles_with_images": total_vehicles_with_images,
            "average_images_per_vehicle": round(avg_images, 1)
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_image_records": 0,
            "vehicles_with_images": 0,
            "average_images_per_vehicle": 0
        }

@api_router.get("/stats")
async def get_stats():
    """Get marketplace statistics including image stats"""
    total_vehicles = await db.vehicles.count_documents({})
    total_dealers = await db.dealers.count_documents({})
    vehicles_with_images = await db.vehicles.count_documents({"images": {"$ne": []}})
    
    # Deal pulse stats
    great_deals = await db.vehicles.count_documents({"deal_pulse_rating": "Great Deal"})
    fair_prices = await db.vehicles.count_documents({"deal_pulse_rating": "Fair Price"})
    high_prices = await db.vehicles.count_documents({"deal_pulse_rating": "High Price"})
    
    # Top makes
    pipeline = [
        {"$group": {"_id": "$make", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_makes = await db.vehicles.aggregate(pipeline).to_list(10)
    
    return {
        "total_vehicles": total_vehicles,
        "total_dealers": total_dealers,
        "vehicles_with_images": vehicles_with_images,
        "image_coverage_percentage": round((vehicles_with_images / total_vehicles * 100) if total_vehicles > 0 else 0, 1),
        "deal_pulse_stats": {
            "great_deals": great_deals,
            "fair_prices": fair_prices,
            "high_prices": high_prices
        },
        "top_makes": [{"make": item["_id"], "count": item["count"]} for item in top_makes]
    }

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