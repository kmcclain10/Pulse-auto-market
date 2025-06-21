from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Dealer Management System", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Enums for structured data
class DealStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class VehicleCondition(str, Enum):
    NEW = "new"
    USED = "used"
    CERTIFIED = "certified"

class VSCTerm(str, Enum):
    MONTHS_12 = "12_months"
    MONTHS_24 = "24_months" 
    MONTHS_36 = "36_months"
    MONTHS_48 = "48_months"
    MONTHS_60 = "60_months"

class VSCCoverage(str, Enum):
    POWERTRAIN = "powertrain"
    BUMPER_TO_BUMPER = "bumper_to_bumper"
    PREMIUM = "premium"


# Vehicle Models
class Vehicle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vin: str
    year: int
    make: str
    model: str
    trim: Optional[str] = None
    condition: VehicleCondition
    mileage: int
    msrp: float
    invoice_price: Optional[float] = None
    selling_price: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TradeIn(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vin: Optional[str] = None
    year: int
    make: str
    model: str
    mileage: int
    condition: str
    estimated_value: float
    payoff_amount: float = 0.0
    net_trade_value: float


# Customer Models
class Customer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    ssn_last_four: Optional[str] = None
    credit_score: Optional[int] = None


# Finance Models
class FinanceTerms(BaseModel):
    loan_amount: float
    apr: float
    term_months: int
    monthly_payment: float
    total_interest: float
    total_cost: float
    down_payment: float = 0.0

class TaxCalculation(BaseModel):
    sales_tax_rate: float
    sales_tax_amount: float
    title_fee: float = 0.0
    license_fee: float = 0.0
    doc_fee: float = 0.0
    total_fees: float


# VSC Models  
class VSCOption(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    coverage_type: VSCCoverage
    term: VSCTerm
    mileage_limit: int
    base_cost: float
    markup: float = 0.0
    final_price: float
    description: str

class GAPOption(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    base_cost: float
    markup: float = 0.0  
    final_price: float
    loan_to_value_ratio: float
    description: str


# Deal Models
class Deal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deal_number: str = Field(default_factory=lambda: f"DEAL-{str(uuid.uuid4())[:8].upper()}")
    status: DealStatus = DealStatus.PENDING
    
    # Related entities
    customer: Customer
    vehicle: Vehicle
    trade_in: Optional[TradeIn] = None
    
    # Financial details
    finance_terms: Optional[FinanceTerms] = None
    tax_calculation: TaxCalculation
    
    # F&I Products
    vsc_options: List[VSCOption] = []
    selected_vsc: Optional[str] = None  # VSC option ID
    gap_option: Optional[GAPOption] = None
    
    # Deal summary
    total_vehicle_price: float
    total_fees_taxes: float
    total_fi_products: float
    total_deal_amount: float
    gross_profit: float = 0.0
    
    # Metadata
    salesperson: Optional[str] = None
    fi_manager: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Create/Update Models
class DealCreate(BaseModel):
    customer: Customer
    vehicle: Vehicle
    trade_in: Optional[TradeIn] = None
    salesperson: Optional[str] = None

class FinanceCalculationRequest(BaseModel):
    loan_amount: float
    apr: float  
    term_months: int
    down_payment: float = 0.0

class MenuSelectionRequest(BaseModel):
    deal_id: str
    selected_vsc_id: Optional[str] = None
    include_gap: bool = False

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
