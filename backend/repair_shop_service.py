"""
Repair Shop Service for Pulse Auto Market
Handles repair shop listings, appointments, and subscriptions
"""
import os
import uuid
import logging
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional
from enum import Enum

from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

class ServiceCategory(str, Enum):
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    BODY_WORK = "body_work"
    TIRES = "tires"
    ELECTRICAL = "electrical"
    ENGINE = "engine"
    TRANSMISSION = "transmission"
    BRAKES = "brakes"
    AC_HEATING = "ac_heating"
    INSPECTION = "inspection"

class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class RepairShopStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class ServiceOffering(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: ServiceCategory
    name: str
    description: str
    estimated_duration: int  # minutes
    price_range_min: float
    price_range_max: float
    popular: bool = False

class BusinessHours(BaseModel):
    monday: Dict[str, str] = {"open": "08:00", "close": "17:00", "closed": False}
    tuesday: Dict[str, str] = {"open": "08:00", "close": "17:00", "closed": False}
    wednesday: Dict[str, str] = {"open": "08:00", "close": "17:00", "closed": False}
    thursday: Dict[str, str] = {"open": "08:00", "close": "17:00", "closed": False}
    friday: Dict[str, str] = {"open": "08:00", "close": "17:00", "closed": False}
    saturday: Dict[str, str] = {"open": "09:00", "close": "15:00", "closed": False}
    sunday: Dict[str, str] = {"open": "00:00", "close": "00:00", "closed": True}

class RepairShop(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    owner_name: str
    owner_email: str
    phone: str
    address: str
    city: str
    state: str
    zip_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Services and specialties
    services: List[ServiceOffering] = []
    specialties: List[str] = []  # e.g., ["BMW", "Mercedes", "Import Cars"]
    certifications: List[str] = []  # e.g., ["ASE Certified", "AAA Approved"]
    
    # Business info
    business_hours: BusinessHours = Field(default_factory=BusinessHours)
    website: Optional[str] = None
    established_year: Optional[int] = None
    num_bays: int = 1
    
    # Images and media
    logo_url: Optional[str] = None
    images: List[str] = []
    
    # Reviews and ratings
    rating: float = 0.0
    review_count: int = 0
    
    # Subscription info
    subscription_active: bool = False
    subscription_expires: Optional[datetime] = None
    featured: bool = False
    
    # Status and metadata
    status: RepairShopStatus = RepairShopStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Appointment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    repair_shop_id: str
    service_id: str
    
    # Customer information
    customer_name: str
    customer_email: str
    customer_phone: str
    
    # Vehicle information
    vehicle_year: Optional[int] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_vin: Optional[str] = None
    
    # Appointment details
    appointment_date: datetime
    estimated_duration: int  # minutes
    service_description: str
    special_requests: str = ""
    
    # Status and updates
    status: AppointmentStatus = AppointmentStatus.PENDING
    confirmed_by_shop: bool = False
    reminder_sent: bool = False
    
    # Pricing (filled by shop)
    estimated_price: Optional[float] = None
    final_price: Optional[float] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RepairShopSubscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    repair_shop_id: str
    shop_name: str
    shop_email: str
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    status: str = "active"  # active, canceled, past_due
    amount: float = 99.0
    billing_cycle: str = "monthly"
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Review(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    repair_shop_id: str
    customer_name: str
    customer_email: str
    rating: int  # 1-5 stars
    title: str
    comment: str
    service_date: Optional[datetime] = None
    verified: bool = False
    helpful_votes: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RepairShopCreate(BaseModel):
    name: str
    description: str
    owner_name: str
    owner_email: str
    phone: str
    address: str
    city: str
    state: str
    zip_code: str
    website: Optional[str] = None
    specialties: List[str] = []
    certifications: List[str] = []

class AppointmentCreate(BaseModel):
    repair_shop_id: str
    service_id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    appointment_date: datetime
    service_description: str
    special_requests: str = ""
    vehicle_year: Optional[int] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None

class RepairShopService:
    """Service for managing repair shops, appointments, and bookings"""
    
    def __init__(self, db):
        self.db = db
        self.subscription_price = 99.0
        
        # Predefined service templates
        self.service_templates = {
            ServiceCategory.MAINTENANCE: [
                {
                    "name": "Oil Change",
                    "description": "Full service oil change with filter replacement",
                    "estimated_duration": 30,
                    "price_range_min": 25.0,
                    "price_range_max": 80.0,
                    "popular": True
                },
                {
                    "name": "Tire Rotation",
                    "description": "Professional tire rotation and pressure check",
                    "estimated_duration": 45,
                    "price_range_min": 20.0,
                    "price_range_max": 50.0,
                    "popular": True
                },
                {
                    "name": "Multi-Point Inspection",
                    "description": "Comprehensive vehicle health check",
                    "estimated_duration": 60,
                    "price_range_min": 50.0,
                    "price_range_max": 100.0,
                    "popular": False
                }
            ],
            ServiceCategory.BRAKES: [
                {
                    "name": "Brake Pad Replacement",
                    "description": "Replace worn brake pads with quality parts",
                    "estimated_duration": 120,
                    "price_range_min": 150.0,
                    "price_range_max": 400.0,
                    "popular": True
                },
                {
                    "name": "Brake Fluid Service",
                    "description": "Brake fluid flush and replacement",
                    "estimated_duration": 60,
                    "price_range_min": 80.0,
                    "price_range_max": 150.0,
                    "popular": False
                }
            ],
            ServiceCategory.TIRES: [
                {
                    "name": "Tire Installation",
                    "description": "Professional tire mounting and balancing",
                    "estimated_duration": 90,
                    "price_range_min": 25.0,
                    "price_range_max": 100.0,
                    "popular": True
                },
                {
                    "name": "Wheel Alignment",
                    "description": "Precision wheel alignment service",
                    "estimated_duration": 90,
                    "price_range_min": 80.0,
                    "price_range_max": 200.0,
                    "popular": True
                }
            ]
        }
    
    async def create_repair_shop(self, shop_data: RepairShopCreate) -> RepairShop:
        """Create a new repair shop listing"""
        try:
            # Check if shop with same email already exists
            existing = await self.db.repair_shops.find_one({"owner_email": shop_data.owner_email})
            if existing:
                raise Exception("Repair shop with this email already exists")
            
            # Create shop object
            shop = RepairShop(**shop_data.dict())
            shop.status = RepairShopStatus.PENDING
            
            # Add some default services based on specialties
            shop.services = self._generate_default_services(shop_data.specialties)
            
            # Save to database
            await self.db.repair_shops.insert_one(shop.dict())
            
            logger.info(f"Created repair shop: {shop.name} ({shop.id})")
            return shop
            
        except Exception as e:
            logger.error(f"Error creating repair shop: {str(e)}")
            raise
    
    def _generate_default_services(self, specialties: List[str]) -> List[ServiceOffering]:
        """Generate default services based on shop specialties"""
        services = []
        
        # Always add basic maintenance
        for service_data in self.service_templates[ServiceCategory.MAINTENANCE]:
            service = ServiceOffering(
                category=ServiceCategory.MAINTENANCE,
                **service_data
            )
            services.append(service)
        
        # Add brake services for most shops
        for service_data in self.service_templates[ServiceCategory.BRAKES][:1]:  # Just brake pads
            service = ServiceOffering(
                category=ServiceCategory.BRAKES,
                **service_data
            )
            services.append(service)
        
        # Add tire services
        for service_data in self.service_templates[ServiceCategory.TIRES]:
            service = ServiceOffering(
                category=ServiceCategory.TIRES,
                **service_data
            )
            services.append(service)
        
        return services
    
    async def get_repair_shops_by_location(self, zip_code: str = None, city: str = None, 
                                         state: str = None, radius_miles: int = 25) -> List[RepairShop]:
        """Get repair shops by location with optional radius"""
        try:
            query = {"status": RepairShopStatus.ACTIVE, "subscription_active": True}
            
            if zip_code:
                # For simplicity, exact zip match. In production, use geospatial queries
                query["zip_code"] = zip_code
            elif city and state:
                query["city"] = {"$regex": city, "$options": "i"}
                query["state"] = {"$regex": state, "$options": "i"}
            
            shops_data = await self.db.repair_shops.find(query).sort([
                ("featured", -1),  # Featured shops first
                ("rating", -1),    # Then by rating
                ("review_count", -1)  # Then by number of reviews
            ]).to_list(50)
            
            return [RepairShop(**shop) for shop in shops_data]
            
        except Exception as e:
            logger.error(f"Error getting repair shops by location: {str(e)}")
            return []
    
    async def search_repair_shops(self, query: str, location: str = None) -> List[RepairShop]:
        """Search repair shops by name, services, or specialties"""
        try:
            search_query = {
                "status": RepairShopStatus.ACTIVE,
                "subscription_active": True,
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"specialties": {"$regex": query, "$options": "i"}},
                    {"services.name": {"$regex": query, "$options": "i"}}
                ]
            }
            
            if location:
                search_query["$and"] = [
                    search_query,
                    {
                        "$or": [
                            {"city": {"$regex": location, "$options": "i"}},
                            {"zip_code": {"$regex": location, "$options": "i"}}
                        ]
                    }
                ]
            
            shops_data = await self.db.repair_shops.find(search_query).sort([
                ("featured", -1),
                ("rating", -1)
            ]).to_list(50)
            
            return [RepairShop(**shop) for shop in shops_data]
            
        except Exception as e:
            logger.error(f"Error searching repair shops: {str(e)}")
            return []
    
    async def get_repair_shop_by_id(self, shop_id: str) -> Optional[RepairShop]:
        """Get repair shop by ID"""
        try:
            shop_data = await self.db.repair_shops.find_one({"id": shop_id})
            if shop_data:
                return RepairShop(**shop_data)
            return None
        except Exception as e:
            logger.error(f"Error getting repair shop {shop_id}: {str(e)}")
            return None
    
    async def update_repair_shop(self, shop_id: str, updates: Dict) -> bool:
        """Update repair shop information"""
        try:
            updates["updated_at"] = datetime.utcnow()
            result = await self.db.repair_shops.update_one(
                {"id": shop_id},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating repair shop {shop_id}: {str(e)}")
            return False
    
    async def create_appointment(self, appointment_data: AppointmentCreate) -> Appointment:
        """Create a new appointment"""
        try:
            # Verify repair shop exists and is active
            shop = await self.get_repair_shop_by_id(appointment_data.repair_shop_id)
            if not shop or shop.status != RepairShopStatus.ACTIVE:
                raise Exception("Repair shop not found or inactive")
            
            # Find the service
            service = None
            for s in shop.services:
                if s.id == appointment_data.service_id:
                    service = s
                    break
            
            if not service:
                raise Exception("Service not found")
            
            # Check if appointment time is available (basic check)
            existing_appointments = await self.db.appointments.find({
                "repair_shop_id": appointment_data.repair_shop_id,
                "appointment_date": {
                    "$gte": appointment_data.appointment_date - timedelta(hours=1),
                    "$lte": appointment_data.appointment_date + timedelta(hours=1)
                },
                "status": {"$in": [AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING]}
            }).to_list(10)
            
            if len(existing_appointments) >= 3:  # Simple capacity check
                raise Exception("No availability at this time")
            
            # Create appointment
            appointment = Appointment(
                **appointment_data.dict(),
                estimated_duration=service.estimated_duration
            )
            
            await self.db.appointments.insert_one(appointment.dict())
            
            logger.info(f"Created appointment: {appointment.id} for shop {shop.name}")
            return appointment
            
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            raise
    
    async def get_shop_appointments(self, shop_id: str, 
                                  date_from: Optional[datetime] = None,
                                  date_to: Optional[datetime] = None) -> List[Appointment]:
        """Get appointments for a repair shop"""
        try:
            query = {"repair_shop_id": shop_id}
            
            if date_from or date_to:
                date_query = {}
                if date_from:
                    date_query["$gte"] = date_from
                if date_to:
                    date_query["$lte"] = date_to
                query["appointment_date"] = date_query
            
            appointments_data = await self.db.appointments.find(query).sort(
                "appointment_date", 1
            ).to_list(100)
            
            return [Appointment(**apt) for apt in appointments_data]
            
        except Exception as e:
            logger.error(f"Error getting appointments for shop {shop_id}: {str(e)}")
            return []
    
    async def update_appointment_status(self, appointment_id: str, 
                                      status: AppointmentStatus, notes: str = "") -> bool:
        """Update appointment status"""
        try:
            updates = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            result = await self.db.appointments.update_one(
                {"id": appointment_id},
                {"$set": updates}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating appointment {appointment_id}: {str(e)}")
            return False
    
    async def add_review(self, shop_id: str, review_data: Dict) -> Review:
        """Add a customer review for a repair shop"""
        try:
            review = Review(
                repair_shop_id=shop_id,
                **review_data
            )
            
            await self.db.reviews.insert_one(review.dict())
            
            # Update shop rating
            await self._update_shop_rating(shop_id)
            
            return review
            
        except Exception as e:
            logger.error(f"Error adding review for shop {shop_id}: {str(e)}")
            raise
    
    async def _update_shop_rating(self, shop_id: str):
        """Update shop's average rating and review count"""
        try:
            # Calculate average rating
            pipeline = [
                {"$match": {"repair_shop_id": shop_id}},
                {"$group": {
                    "_id": None,
                    "avg_rating": {"$avg": "$rating"},
                    "count": {"$sum": 1}
                }}
            ]
            
            result = await self.db.reviews.aggregate(pipeline).to_list(1)
            
            if result:
                avg_rating = round(result[0]["avg_rating"], 1)
                review_count = result[0]["count"]
                
                await self.db.repair_shops.update_one(
                    {"id": shop_id},
                    {"$set": {
                        "rating": avg_rating,
                        "review_count": review_count,
                        "updated_at": datetime.utcnow()
                    }}
                )
                
        except Exception as e:
            logger.error(f"Error updating shop rating for {shop_id}: {str(e)}")
    
    async def get_shop_reviews(self, shop_id: str, limit: int = 10) -> List[Review]:
        """Get reviews for a repair shop"""
        try:
            reviews_data = await self.db.reviews.find(
                {"repair_shop_id": shop_id}
            ).sort("created_at", -1).limit(limit).to_list(limit)
            
            return [Review(**review) for review in reviews_data]
            
        except Exception as e:
            logger.error(f"Error getting reviews for shop {shop_id}: {str(e)}")
            return []
    
    async def create_subscription(self, shop_id: str) -> RepairShopSubscription:
        """Create subscription for repair shop"""
        try:
            shop = await self.get_repair_shop_by_id(shop_id)
            if not shop:
                raise Exception("Repair shop not found")
            
            # Check if subscription already exists
            existing = await self.db.repair_shop_subscriptions.find_one({"repair_shop_id": shop_id})
            if existing:
                raise Exception("Subscription already exists")
            
            # Create subscription
            subscription = RepairShopSubscription(
                repair_shop_id=shop_id,
                shop_name=shop.name,
                shop_email=shop.owner_email,
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                trial_end=datetime.utcnow() + timedelta(days=7)  # 7-day trial
            )
            
            await self.db.repair_shop_subscriptions.insert_one(subscription.dict())
            
            # Activate shop
            await self.update_repair_shop(shop_id, {
                "subscription_active": True,
                "status": RepairShopStatus.ACTIVE
            })
            
            return subscription
            
        except Exception as e:
            logger.error(f"Error creating subscription for shop {shop_id}: {str(e)}")
            raise
    
    async def get_available_time_slots(self, shop_id: str, date: datetime) -> List[str]:
        """Get available appointment time slots for a specific date"""
        try:
            shop = await self.get_repair_shop_by_id(shop_id)
            if not shop:
                return []
            
            # Get business hours for the day
            day_name = date.strftime("%A").lower()
            business_hours = getattr(shop.business_hours, day_name)
            
            if business_hours.get("closed", True):
                return []
            
            # Generate time slots (every hour)
            open_time = datetime.strptime(business_hours["open"], "%H:%M").time()
            close_time = datetime.strptime(business_hours["close"], "%H:%M").time()
            
            time_slots = []
            current_time = datetime.combine(date.date(), open_time)
            end_time = datetime.combine(date.date(), close_time)
            
            while current_time < end_time:
                # Check if slot is available
                existing = await self.db.appointments.find({
                    "repair_shop_id": shop_id,
                    "appointment_date": {
                        "$gte": current_time,
                        "$lt": current_time + timedelta(hours=1)
                    },
                    "status": {"$in": [AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING]}
                }).to_list(1)
                
                if not existing:
                    time_slots.append(current_time.strftime("%H:%M"))
                
                current_time += timedelta(hours=1)
            
            return time_slots
            
        except Exception as e:
            logger.error(f"Error getting time slots for shop {shop_id}: {str(e)}")
            return []
    
    async def get_repair_shop_stats(self) -> Dict:
        """Get repair shop marketplace statistics"""
        try:
            total_shops = await self.db.repair_shops.count_documents({})
            active_shops = await self.db.repair_shops.count_documents({"status": "active"})
            total_appointments = await self.db.appointments.count_documents({})
            
            # Popular services
            popular_services = await self.db.appointments.aggregate([
                {"$group": {"_id": "$service_description", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]).to_list(5)
            
            return {
                "total_shops": total_shops,
                "active_shops": active_shops,
                "total_appointments": total_appointments,
                "popular_services": popular_services
            }
            
        except Exception as e:
            logger.error(f"Error getting repair shop stats: {str(e)}")
            return {}