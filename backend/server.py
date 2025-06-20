from fastapi import FastAPI, APIRouter, HTTPException, Query, BackgroundTasks, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
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

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

# Import our enhanced services
from image_service import VehicleImageManager
from ai_crm_service import AICRMService, Lead, LeadStatus, LeadScore, InquiryType, ConversationMessage
from desking_service import DeskingService, DealCalculation, DealType, PaymentGrid, FIProduct, TradeIn, TaxInfo, FinanceTerms, LeaseTerms
from billing_service import BillingService, Subscription, SubscriptionPlan, SubscriptionStatus, PaymentHistory, CreateSubscriptionRequest, UpdateSubscriptionRequest
from repair_shop_service import RepairShopService, RepairShop, Appointment, Review, ServiceCategory, AppointmentStatus, RepairShopCreate, AppointmentCreate

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
billing_service = BillingService(db)
repair_shop_service = RepairShopService(db)

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

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    await image_manager.initialize()
    logging.info("All services initialized: Image Manager, AI CRM, Desking Tool, Billing System, Repair Shops")

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
    
    # CRM stats
    total_leads = await db.leads.count_documents({})
    hot_leads = await db.leads.count_documents({"lead_score": "hot"})
    
    # Desking stats
    total_deals = await db.deals.count_documents({})
    
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
        "crm_stats": {
            "total_leads": total_leads,
            "hot_leads": hot_leads
        },
        "desking_stats": {
            "total_deals": total_deals
        },
        "top_makes": [{"make": item["_id"], "count": item["count"]} for item in top_makes]
    }

# AI CRM Routes
@api_router.post("/leads", response_model=Lead)
async def create_lead(lead_data: dict, background_tasks: BackgroundTasks):
    """Create a new lead and generate AI response"""
    try:
        lead = await ai_crm_service.process_new_lead(lead_data)
        return lead
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating lead: {str(e)}")

@api_router.get("/leads/dealer/{dealer_id}", response_model=List[Lead])
async def get_dealer_leads(dealer_id: str, status: Optional[LeadStatus] = Query(None), limit: int = Query(50, le=100)):
    """Get leads for a specific dealer"""
    leads = await ai_crm_service.get_leads_for_dealer(dealer_id, status, limit)
    return leads

@api_router.put("/leads/{lead_id}/status")
async def update_lead_status(lead_id: str, status: LeadStatus, notes: str = ""):
    """Update lead status"""
    success = await ai_crm_service.update_lead_status(lead_id, status, notes)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead status updated", "lead_id": lead_id, "status": status}

@api_router.post("/leads/{lead_id}/approve-response")
async def approve_ai_response(lead_id: str, approved: bool = True, custom_response: Optional[str] = None):
    """Approve or modify AI response"""
    success = await ai_crm_service.approve_ai_response(lead_id, approved, custom_response)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "AI response approved", "lead_id": lead_id, "approved": approved}

@api_router.get("/leads/{lead_id}/conversation", response_model=List[ConversationMessage])
async def get_conversation_history(lead_id: str):
    """Get conversation history for a lead"""
    # First get the lead to find conversation_id
    lead_data = await db.leads.find_one({"id": lead_id})
    if not lead_data:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    conversation = await ai_crm_service.get_conversation_history(lead_data["conversation_id"])
    return conversation

@api_router.get("/leads/dealer/{dealer_id}/follow-ups")
async def get_follow_up_suggestions(dealer_id: str):
    """Get AI-generated follow-up suggestions"""
    suggestions = await ai_crm_service.generate_follow_up_sequences(dealer_id)
    return {"follow_up_suggestions": suggestions}

@api_router.get("/crm/dealer/{dealer_id}/stats")
async def get_dealer_crm_stats(dealer_id: str):
    """Get CRM statistics for a dealer"""
    stats = await ai_crm_service.get_dealer_crm_stats(dealer_id)
    return stats

# Advanced Desking Tool Routes
@api_router.post("/deals", response_model=DealCalculation)
async def create_deal(deal_data: dict):
    """Create a new deal calculation"""
    try:
        deal = await desking_service.calculate_deal(deal_data)
        return deal
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating deal: {str(e)}")

@api_router.get("/deals/dealer/{dealer_id}", response_model=List[DealCalculation])
async def get_dealer_deals(dealer_id: str, limit: int = Query(50, le=100)):
    """Get deals for a specific dealer"""
    deals = await desking_service.get_dealer_deals(dealer_id, limit)
    return deals

@api_router.get("/deals/{deal_id}", response_model=DealCalculation)
async def get_deal_by_id(deal_id: str):
    """Get a specific deal by ID"""
    deal = await desking_service.get_deal_by_id(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal

@api_router.put("/deals/{deal_id}")
async def update_deal(deal_id: str, updates: dict):
    """Update an existing deal"""
    success = await desking_service.update_deal(deal_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"message": "Deal updated", "deal_id": deal_id}

@api_router.post("/deals/payment-grid", response_model=PaymentGrid)
async def generate_payment_grid(
    vehicle_price: float,
    down_payment: float = 0.0,
    trade_value: float = 0.0,
    tax_rate: float = 8.25
):
    """Generate payment grid with multiple term/rate combinations"""
    grid = await desking_service.generate_payment_grid(vehicle_price, down_payment, trade_value, tax_rate)
    return grid

@api_router.get("/deals/{deal_id}/proposal")
async def get_deal_proposal(deal_id: str):
    """Get formatted deal proposal for customer presentation"""
    proposal = await desking_service.create_deal_proposal(deal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return proposal

@api_router.get("/fi-products/dealer/{dealer_id}")
async def get_dealer_fi_products(dealer_id: str, vehicle_price: float, term_months: int = 60):
    """Get F&I product menu for a dealer"""
    products = desking_service.create_fi_product_menu(dealer_id, vehicle_price, term_months)
    return {"products": [product.dict() for product in products]}

@api_router.get("/desking/dealer/{dealer_id}/stats")
async def get_dealer_fi_stats(dealer_id: str):
    """Get F&I and desking statistics for a dealer"""
    stats = await desking_service.get_dealer_fi_stats(dealer_id)
    return stats

@api_router.post("/deals/calculate-payment")
async def calculate_payment(
    principal: float,
    rate: float,
    months: int,
    frequency: str = "monthly"
):
    """Calculate loan payment"""
    from desking_service import PaymentFrequency
    
    freq_map = {
        "monthly": PaymentFrequency.MONTHLY,
        "biweekly": PaymentFrequency.BIWEEKLY,
        "weekly": PaymentFrequency.WEEKLY
    }
    
    payment_freq = freq_map.get(frequency, PaymentFrequency.MONTHLY)
    payment = desking_service.calculate_finance_payment(principal, rate, months, payment_freq)
    
    return {
        "principal": principal,
        "rate": rate,
        "months": months,
        "frequency": frequency,
        "payment": payment
    }

# Vehicle inquiry endpoint (triggers AI CRM)
@api_router.post("/vehicles/{vin}/inquire")
async def create_vehicle_inquiry(vin: str, inquiry_data: dict, background_tasks: BackgroundTasks):
    """Create a vehicle inquiry (triggers AI CRM response)"""
    try:
        # Add VIN to inquiry data
        inquiry_data["vehicle_vin"] = vin
        
        # Process through AI CRM
        lead = await ai_crm_service.process_new_lead(inquiry_data)
        
        # Track usage for billing
        if inquiry_data.get("dealer_id"):
            await billing_service.track_usage(inquiry_data["dealer_id"], "leads_processed")
        
        return {
            "message": "Inquiry received and processed",
            "lead_id": lead.id,
            "ai_response_generated": True,
            "lead_score": lead.lead_score,
            "inquiry_type": lead.inquiry_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing inquiry: {str(e)}")

# Subscription Billing Routes
@api_router.post("/subscriptions/create")
async def create_subscription(request: CreateSubscriptionRequest):
    """Create a new subscription with 90-day free trial"""
    try:
        result = await billing_service.create_subscription(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/subscriptions/dealer/{dealer_id}", response_model=Subscription)
async def get_dealer_subscription(dealer_id: str):
    """Get subscription for a dealer"""
    subscription = await billing_service.get_subscription_by_dealer(dealer_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    return subscription

@api_router.put("/subscriptions/update")
async def update_subscription(request: UpdateSubscriptionRequest):
    """Update subscription plan"""
    try:
        result = await billing_service.update_subscription_plan(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(subscription_id: str, immediate: bool = Query(False)):
    """Cancel subscription"""
    try:
        result = await billing_service.cancel_subscription(subscription_id, immediate)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/billing/dealer/{dealer_id}/history", response_model=List[PaymentHistory])
async def get_payment_history(dealer_id: str, limit: int = Query(50, le=100)):
    """Get payment history for a dealer"""
    payments = await billing_service.get_payment_history(dealer_id, limit)
    return payments

@api_router.post("/billing/dealer/{dealer_id}/portal")
async def create_billing_portal_session(dealer_id: str):
    """Create Stripe billing portal session"""
    try:
        portal_url = await billing_service.create_billing_portal_session(dealer_id)
        return {"portal_url": portal_url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/billing/dealer/{dealer_id}/summary")
async def get_billing_summary(dealer_id: str):
    """Get comprehensive billing summary"""
    summary = await billing_service.get_billing_summary(dealer_id)
    return summary

@api_router.get("/billing/dealer/{dealer_id}/usage")
async def check_usage_limits(dealer_id: str):
    """Check usage limits for dealer"""
    usage_info = await billing_service.check_usage_limits(dealer_id)
    return usage_info

@api_router.get("/plans")
async def get_subscription_plans():
    """Get all available subscription plans"""
    plans = billing_service.get_plans()
    return {"plans": plans}

# Stripe Webhook Handler
@api_router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    try:
        import stripe
        
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        if not webhook_secret:
            logger.warning("Stripe webhook secret not configured")
            return {"status": "webhook secret not configured"}
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Handle the event
        await billing_service.handle_webhook_event(event)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error handling Stripe webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

# Enhanced dealer management with subscription info
@api_router.get("/dealers/with-subscriptions")
async def get_dealers_with_subscriptions():
    """Get all dealers with their subscription information"""
    try:
        dealers = await db.dealers.find().to_list(1000)
        dealers_with_subs = []
        
        for dealer in dealers:
            subscription = await billing_service.get_subscription_by_dealer(dealer['id'])
            dealer_info = {
                **dealer,
                "subscription": subscription.dict() if subscription else None,
                "subscription_status": subscription.status if subscription else "none",
                "plan": subscription.plan if subscription else None
            }
            dealers_with_subs.append(dealer_info)
        
        return dealers_with_subs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dealers: {str(e)}")

# Middleware to check subscription status (add to routes that need limits)
async def check_subscription_middleware(dealer_id: str, feature_type: str):
    """Check if dealer has valid subscription and is within limits"""
    try:
        subscription = await billing_service.get_subscription_by_dealer(dealer_id)
        if not subscription:
            return {"allowed": False, "message": "No active subscription"}
        
        if subscription.status not in ["active", "trialing"]:
            return {"allowed": False, "message": "Subscription not active"}
        
        # Check usage limits
        usage_info = await billing_service.check_usage_limits(dealer_id)
        if not usage_info["within_limits"]:
            return {"allowed": False, "message": "Usage limits exceeded", "details": usage_info["blocked"]}
        
        return {"allowed": True, "usage_info": usage_info}
        
    except Exception as e:
        logger.error(f"Error checking subscription for dealer {dealer_id}: {str(e)}")
        return {"allowed": False, "message": "Error checking subscription"}

# Protected route example (with usage tracking)
@api_router.post("/vehicles/protected", response_model=Vehicle)
async def create_vehicle_protected(vehicle: VehicleCreate, background_tasks: BackgroundTasks):
    """Create a new vehicle listing (subscription required)"""
    # Check subscription
    if not vehicle.dealer_name:
        raise HTTPException(status_code=400, detail="Dealer information required")
    
    # Find dealer ID (in real app, this would come from auth)
    dealer = await db.dealers.find_one({"name": vehicle.dealer_name})
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
    
    # Check subscription limits
    subscription_check = await check_subscription_middleware(dealer['id'], "vehicles")
    if not subscription_check["allowed"]:
        raise HTTPException(status_code=403, detail=subscription_check["message"])
    
    # Create vehicle (existing logic)
    vehicle_dict = vehicle.dict()
    vehicle_obj = Vehicle(**vehicle_dict)
    
    # Calculate Deal Pulse rating
    existing_vehicles = await db.vehicles.find().to_list(1000)
    market_analysis = calculate_deal_pulse(vehicle_dict, existing_vehicles)
    vehicle_obj.deal_pulse_rating = market_analysis['rating']
    vehicle_obj.market_price_analysis = market_analysis
    
    # Insert vehicle
    await db.vehicles.insert_one(vehicle_obj.dict())
    
    # Track usage for billing
    await billing_service.track_usage(dealer['id'], "vehicles_listed")
    
    # Trigger image scraping in background if URL provided
    if vehicle.scraped_from_url:
        background_tasks.add_task(
            image_manager.scrape_and_store_images,
            vehicle_obj.id,
            vehicle_obj.vin,
            vehicle.scraped_from_url
        )
    
    return vehicle_obj

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