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
import base64
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch


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

class FormType(str, Enum):
    CREDIT_APPLICATION = "credit_application"
    PURCHASE_AGREEMENT = "purchase_agreement"
    FINANCE_CONTRACT = "finance_contract"
    TITLE_REGISTRATION = "title_registration"
    INSURANCE_CERTIFICATE = "insurance_certificate"
    WINDOW_STICKER = "window_sticker"
    ODOMETER_DISCLOSURE = "odometer_disclosure"
    LEMON_LAW = "lemon_law"

class FormStatus(str, Enum):
    DRAFT = "draft"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    COMPLETED = "completed"

class LenderStatus(str, Enum):
    SUBMITTED = "submitted"
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    CONDITIONAL = "conditional"

class DocumentStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    SENT_FOR_SIGNATURE = "sent_for_signature"
    SIGNED = "signed"
    FINALIZED = "finalized"


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

# Business Logic Functions
def calculate_finance_payment(loan_amount: float, apr: float, term_months: int) -> Dict[str, float]:
    """Calculate monthly payment and total interest for a loan"""
    if apr == 0:
        monthly_payment = loan_amount / term_months
        total_interest = 0
    else:
        monthly_rate = apr / 12 / 100
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
        total_interest = (monthly_payment * term_months) - loan_amount
    
    return {
        "monthly_payment": round(monthly_payment, 2),
        "total_interest": round(total_interest, 2),
        "total_cost": round(loan_amount + total_interest, 2)
    }

def calculate_sales_tax(vehicle_price: float, state: str = "CA") -> TaxCalculation:
    """Calculate sales tax and fees based on state"""
    # Default California rates - can be expanded for other states
    tax_rates = {
        "CA": {"sales_tax": 0.0725, "title": 23.0, "license": 65.0, "doc": 85.0},
        "TX": {"sales_tax": 0.0625, "title": 33.0, "license": 51.75, "doc": 150.0},
        "FL": {"sales_tax": 0.06, "title": 77.25, "license": 48.0, "doc": 199.0},
        "NY": {"sales_tax": 0.08, "title": 50.0, "license": 25.0, "doc": 175.0}
    }
    
    rates = tax_rates.get(state, tax_rates["CA"])
    sales_tax_amount = vehicle_price * rates["sales_tax"]
    
    return TaxCalculation(
        sales_tax_rate=rates["sales_tax"],
        sales_tax_amount=round(sales_tax_amount, 2),
        title_fee=rates["title"],
        license_fee=rates["license"], 
        doc_fee=rates["doc"],
        total_fees=round(sales_tax_amount + rates["title"] + rates["license"] + rates["doc"], 2)
    )

def generate_vsc_options(vehicle: Vehicle) -> List[VSCOption]:
    """Generate VSC options based on vehicle details"""
    base_costs = {
        VSCCoverage.POWERTRAIN: {"12_months": 895, "24_months": 1295, "36_months": 1695, "48_months": 2095, "60_months": 2495},
        VSCCoverage.BUMPER_TO_BUMPER: {"12_months": 1495, "24_months": 1995, "36_months": 2495, "48_months": 2995, "60_months": 3495},
        VSCCoverage.PREMIUM: {"12_months": 1995, "24_months": 2695, "36_months": 3395, "48_months": 4095, "60_months": 4795}
    }
    
    mileage_limits = {
        VSCCoverage.POWERTRAIN: 100000,
        VSCCoverage.BUMPER_TO_BUMPER: 75000,
        VSCCoverage.PREMIUM: 100000
    }
    
    options = []
    for coverage in VSCCoverage:
        for term in VSCTerm:
            base_cost = base_costs[coverage][term.value]
            markup = base_cost * 0.25  # 25% markup
            
            # Adjust pricing based on vehicle age/mileage
            age_factor = max(0.8, 1 - (2024 - vehicle.year) * 0.05)
            mileage_factor = max(0.8, 1 - (vehicle.mileage / 100000) * 0.2)
            adjusted_cost = base_cost * age_factor * mileage_factor
            
            options.append(VSCOption(
                coverage_type=coverage,
                term=term,
                mileage_limit=mileage_limits[coverage],
                base_cost=round(adjusted_cost, 2),
                markup=round(markup, 2),
                final_price=round(adjusted_cost + markup, 2),
                description=f"{coverage.value.replace('_', ' ').title()} - {term.value.replace('_', ' ')} - {mileage_limits[coverage]:,} miles"
            ))
    
    return options

def generate_gap_option(loan_amount: float, vehicle_value: float) -> GAPOption:
    """Generate GAP insurance option"""
    ltv_ratio = loan_amount / vehicle_value if vehicle_value > 0 else 0
    base_cost = min(1295, max(695, loan_amount * 0.05))  # 5% of loan amount, min $695, max $1295
    markup = base_cost * 0.30  # 30% markup
    
    return GAPOption(
        base_cost=round(base_cost, 2),
        markup=round(markup, 2),
        final_price=round(base_cost + markup, 2),
        loan_to_value_ratio=round(ltv_ratio, 4),
        description=f"GAP Insurance - LTV: {ltv_ratio:.1%}"
    )


# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "Dealer Management System API - F&I Desking Tool"}

# Deal Management Endpoints
@api_router.post("/deals", response_model=Deal)
async def create_deal(deal_data: DealCreate):
    """Create a new deal"""
    try:
        # Calculate tax and fees
        customer_state = deal_data.customer.state or "CA"
        tax_calc = calculate_sales_tax(deal_data.vehicle.selling_price, customer_state)
        
        # Calculate net trade value
        net_trade_value = 0.0
        if deal_data.trade_in:
            net_trade_value = deal_data.trade_in.estimated_value - deal_data.trade_in.payoff_amount
            deal_data.trade_in.net_trade_value = net_trade_value
        
        # Generate VSC options
        vsc_options = generate_vsc_options(deal_data.vehicle)
        
        # Calculate totals
        total_vehicle_price = deal_data.vehicle.selling_price - net_trade_value
        total_fees_taxes = tax_calc.total_fees
        
        # Create deal
        deal = Deal(
            customer=deal_data.customer,
            vehicle=deal_data.vehicle,
            trade_in=deal_data.trade_in,
            tax_calculation=tax_calc,
            vsc_options=vsc_options,
            total_vehicle_price=total_vehicle_price,
            total_fees_taxes=total_fees_taxes,
            total_fi_products=0.0,
            total_deal_amount=total_vehicle_price + total_fees_taxes,
            salesperson=deal_data.salesperson
        )
        
        # Save to database
        deal_dict = deal.dict()
        await db.deals.insert_one(deal_dict)
        
        return deal
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/deals", response_model=List[Deal])
async def get_deals():
    """Get all deals"""
    deals = await db.deals.find().to_list(1000)
    return [Deal(**deal) for deal in deals]

@api_router.get("/deals/{deal_id}", response_model=Deal)
async def get_deal(deal_id: str):
    """Get a specific deal"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return Deal(**deal)

@api_router.put("/deals/{deal_id}/status")
async def update_deal_status(deal_id: str, status: DealStatus):
    """Update deal status"""
    result = await db.deals.update_one(
        {"id": deal_id},
        {"$set": {"status": status.value, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"message": "Deal status updated successfully"}

# Finance Calculation Endpoints
@api_router.post("/finance/calculate")
async def calculate_finance(request: FinanceCalculationRequest):
    """Calculate finance terms"""
    calc = calculate_finance_payment(request.loan_amount, request.apr, request.term_months)
    
    return FinanceTerms(
        loan_amount=request.loan_amount,
        apr=request.apr,
        term_months=request.term_months,
        monthly_payment=calc["monthly_payment"],
        total_interest=calc["total_interest"],
        total_cost=calc["total_cost"],
        down_payment=request.down_payment
    )

@api_router.post("/deals/{deal_id}/finance")
async def add_finance_terms(deal_id: str, finance_request: FinanceCalculationRequest):
    """Add finance terms to a deal"""
    calc = calculate_finance_payment(finance_request.loan_amount, finance_request.apr, finance_request.term_months)
    
    finance_terms = FinanceTerms(
        loan_amount=finance_request.loan_amount,
        apr=finance_request.apr,
        term_months=finance_request.term_months,
        monthly_payment=calc["monthly_payment"],
        total_interest=calc["total_interest"],
        total_cost=calc["total_cost"],
        down_payment=finance_request.down_payment
    )
    
    # Update deal
    result = await db.deals.update_one(
        {"id": deal_id},
        {"$set": {"finance_terms": finance_terms.dict(), "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    return finance_terms

# F&I Product Endpoints
@api_router.post("/deals/{deal_id}/menu-selection")
async def update_menu_selection(deal_id: str, selection: MenuSelectionRequest):
    """Update F&I product selection for a deal"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    deal_obj = Deal(**deal)
    
    # Calculate F&I products total
    fi_total = 0.0
    
    # Add selected VSC
    if selection.selected_vsc_id:
        selected_vsc = next((vsc for vsc in deal_obj.vsc_options if vsc.id == selection.selected_vsc_id), None)
        if selected_vsc:
            fi_total += selected_vsc.final_price
    
    # Add GAP if selected
    gap_option = None
    if selection.include_gap:
        # Calculate loan amount for GAP
        loan_amount = deal_obj.total_vehicle_price + deal_obj.total_fees_taxes
        if deal_obj.finance_terms:
            loan_amount = deal_obj.finance_terms.loan_amount
        
        gap_option = generate_gap_option(loan_amount, deal_obj.vehicle.selling_price)
        fi_total += gap_option.final_price
    
    # Update deal
    update_data = {
        "selected_vsc": selection.selected_vsc_id,
        "gap_option": gap_option.dict() if gap_option else None,
        "total_fi_products": fi_total,
        "total_deal_amount": deal_obj.total_vehicle_price + deal_obj.total_fees_taxes + fi_total,
        "updated_at": datetime.utcnow()
    }
    
    await db.deals.update_one({"id": deal_id}, {"$set": update_data})
    
    return {"message": "Menu selection updated successfully", "total_fi_products": fi_total}

@api_router.get("/deals/{deal_id}/menu")
async def get_deal_menu(deal_id: str):
    """Get F&I menu for a deal"""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    deal_obj = Deal(**deal)
    
    # Generate GAP option if not exists
    loan_amount = deal_obj.total_vehicle_price + deal_obj.total_fees_taxes
    if deal_obj.finance_terms:
        loan_amount = deal_obj.finance_terms.loan_amount
    
    gap_option = generate_gap_option(loan_amount, deal_obj.vehicle.selling_price)
    
    return {
        "deal_id": deal_id,
        "vsc_options": deal_obj.vsc_options,
        "gap_option": gap_option,
        "selected_vsc": deal_obj.selected_vsc,
        "has_gap": bool(deal_obj.gap_option)
    }


# Old endpoints for backward compatibility
@api_router.post("/status", response_model=dict)
async def create_status_check(input: dict):
    return {"message": "Legacy endpoint - use /deals instead"}

@api_router.get("/status", response_model=List[dict])
async def get_status_checks():
    return [{"message": "Legacy endpoint - use /deals instead"}]


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
