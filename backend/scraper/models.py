from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class Vehicle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic vehicle info
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    price: Optional[float] = None
    mileage: Optional[int] = None
    vin: Optional[str] = None
    
    # Additional details
    body_type: Optional[str] = None
    transmission: Optional[str] = None
    engine: Optional[str] = None
    fuel_type: Optional[str] = None
    drivetrain: Optional[str] = None
    exterior_color: Optional[str] = None
    interior_color: Optional[str] = None
    
    # Photos and media
    photos: List[str] = Field(default_factory=list)
    photo_count: int = 0
    
    # Description and features
    description: Optional[str] = None
    features: List[str] = Field(default_factory=list)
    
    # Dealer information
    dealer_name: Optional[str] = None
    dealer_url: str
    dealer_phone: Optional[str] = None
    dealer_address: Optional[str] = None
    dealer_city: Optional[str] = None
    dealer_state: Optional[str] = None
    dealer_zip: Optional[str] = None
    
    # Vehicle listing details
    stock_number: Optional[str] = None
    vehicle_url: Optional[str] = None
    
    # Scraping metadata
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    scraping_job_id: Optional[str] = None
    
    # Data quality indicators
    data_completeness: float = 0.0  # Percentage of fields populated
    has_multiple_photos: bool = False
    has_detailed_specs: bool = False

class ScrapingJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dealer_urls: List[str]
    status: str = "pending"  # pending, running, completed, failed
    progress: int = 0  # 0-100
    max_vehicles_per_dealer: int = 100
    
    # Results
    dealers_completed: int = 0
    total_vehicles_scraped: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Error handling
    error_message: Optional[str] = None
    
    # Job configuration
    scraper_config: Dict[str, Any] = Field(default_factory=dict)

class DealerInfo(BaseModel):
    name: Optional[str] = None
    url: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    inventory_count: int = 0
    last_scraped: Optional[datetime] = None
    success_rate: float = 0.0
    
    # Website analysis
    site_type: Optional[str] = None  # wordpress, custom, dealercarsearch, etc.
    has_inventory_page: bool = False
    inventory_url: Optional[str] = None
    requires_javascript: bool = False
    anti_bot_protection: bool = False