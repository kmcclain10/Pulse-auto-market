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
from bson import ObjectId


# Custom ObjectId handler for Pydantic
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


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
    # Core Purchase Documents
    PURCHASE_AGREEMENT = "purchase_agreement"  # Car Purchase Agreement / Buyer's Order
    BUYERS_ORDER = "buyers_order"
    
    # Federal Required Documents
    ODOMETER_DISCLOSURE = "odometer_disclosure"  # Federal requirement
    TRUTH_IN_LENDING = "truth_in_lending"  # TILA Disclosure
    
    # Title & Registration
    TITLE_TRANSFER = "title_transfer"
    TITLE_APPLICATION = "title_application"
    REGISTRATION_APPLICATION = "registration_application"
    
    # Financing Documents
    FINANCE_CONTRACT = "finance_contract"  # Loan Agreement
    LOAN_APPLICATION = "loan_application"
    CREDIT_APPLICATION = "credit_application"
    PROMISSORY_NOTE = "promissory_note"
    SECURITY_AGREEMENT = "security_agreement"
    
    # Disclosure Documents
    DAMAGE_DISCLOSURE = "damage_disclosure"  # For used cars
    LEMON_LAW_DISCLOSURE = "lemon_law_disclosure"
    AS_IS_DISCLOSURE = "as_is_disclosure"
    WARRANTIES_DISCLOSURE = "warranties_disclosure"
    
    # Trade-in Documents
    TRADE_IN_APPRAISAL = "trade_in_appraisal"
    TRADE_IN_AGREEMENT = "trade_in_agreement"
    TRADE_IN_TITLE = "trade_in_title"
    TRADE_IN_PAYOFF = "trade_in_payoff"
    
    # F&I Products
    EXTENDED_WARRANTY = "extended_warranty"  # Extended Warranty Contract
    VSC_CONTRACT = "vsc_contract"  # Vehicle Service Contract
    GAP_INSURANCE = "gap_insurance"
    
    # Rebates & Incentives
    MANUFACTURER_REBATE = "manufacturer_rebate"
    DEALER_REBATE = "dealer_rebate"
    INCENTIVE_ASSIGNMENT = "incentive_assignment"
    CASH_BACK_FORM = "cash_back_form"
    
    # Insurance Documents
    INSURANCE_CERTIFICATE = "insurance_certificate"
    INSURANCE_VERIFICATION = "insurance_verification"
    
    # Additional Required Forms
    WINDOW_STICKER = "window_sticker"  # Monroney Label
    BILL_OF_SALE = "bill_of_sale"
    SALES_TAX_FORM = "sales_tax_form"
    POWER_OF_ATTORNEY = "power_of_attorney"
    
    # State-Specific Forms
    SMOG_CERTIFICATE = "smog_certificate"  # CA
    SAFETY_INSPECTION = "safety_inspection"  # Various states
    VIN_VERIFICATION = "vin_verification"
    
    # Customer Documents
    DELIVERY_RECEIPT = "delivery_receipt"
    KEYS_RECEIPT = "keys_receipt"
    MANUAL_RECEIPT = "manual_receipt"

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


# Forms Management Models
class FormTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    form_type: FormType
    state: str  # State code (e.g., "CA", "TX")
    version: str = "1.0"
    title: str
    description: str
    fields: List[Dict[str, Any]]  # Dynamic form fields
    compliance_notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FormData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str
    form_template_id: str
    form_type: FormType
    status: FormStatus = FormStatus.DRAFT
    field_values: Dict[str, Any] = {}
    signatures: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Bank Integration Models
class Lender(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str  # Lender identifier
    api_endpoint: Optional[str] = None
    is_active: bool = True
    min_credit_score: Optional[int] = None
    max_ltv: Optional[float] = None
    interest_rates: Dict[str, float] = {}  # Term-based rates
    specialties: List[str] = []  # e.g., ["subprime", "luxury", "commercial"]

class CreditApplication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str
    customer_id: str
    
    # Personal Information
    ssn: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    employment_status: Optional[str] = None
    employer_name: Optional[str] = None
    monthly_income: Optional[float] = None
    housing_status: Optional[str] = None  # rent, own, other
    monthly_housing_payment: Optional[float] = None
    
    # Co-applicant Information
    co_applicant: Optional[Dict[str, Any]] = None
    
    # Loan Details
    requested_amount: float
    requested_term: int
    down_payment: float = 0.0
    
    # Status
    status: str = "draft"
    submitted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LenderSubmission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str
    credit_application_id: str
    lender_id: str
    
    # Submission Details
    submitted_data: Dict[str, Any]
    status: LenderStatus = LenderStatus.SUBMITTED
    
    # Response Details
    decision: Optional[str] = None
    approved_amount: Optional[float] = None
    approved_rate: Optional[float] = None
    approved_term: Optional[int] = None
    stipulations: List[str] = []
    decline_reason: Optional[str] = None
    
    # Timestamps
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = None

# Document Generation Models
class DocumentTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    document_type: str
    template_content: str  # HTML or template format
    variables: List[str]  # List of variable names used in template
    state_specific: bool = False
    states: List[str] = []  # If state_specific, which states
    version: str = "1.0"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GeneratedDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str
    template_id: str
    document_type: str
    title: str
    
    # Content
    generated_content: str  # HTML content
    pdf_content: Optional[str] = None  # Base64 encoded PDF
    variables_used: Dict[str, Any] = {}
    
    # Status & Signatures
    status: DocumentStatus = DocumentStatus.DRAFT
    signature_required: bool = False
    signatures: List[Dict[str, Any]] = []
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# E-Signature Models
class SignatureRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    deal_id: str
    
    # Signers
    signers: List[Dict[str, Any]]  # List of people who need to sign
    
    # Configuration
    signing_order: List[str] = []  # Order of signing if sequential
    expires_at: Optional[datetime] = None
    
    # Status
    status: str = "pending"
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Signature(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    signature_request_id: str
    document_id: str
    signer_email: str
    signer_name: str
    
    # Signature Data
    signature_data: Optional[str] = None  # Base64 encoded signature image
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    signed_at: Optional[datetime] = None
    
    # Legal
    legal_notice_acknowledged: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Update the main Deal model to include new relationships
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
    
    # NEW: Forms & Documents
    forms: List[str] = []  # Form IDs
    documents: List[str] = []  # Document IDs
    credit_applications: List[str] = []  # Credit Application IDs
    lender_submissions: List[str] = []  # Lender Submission IDs
    
    # Deal summary
    total_vehicle_price: float
    total_fees_taxes: float
    total_fi_products: float
    total_deal_amount: float
    gross_profit: float = 0.0
    
    # Workflow status
    forms_completed: bool = False
    docs_generated: bool = False
    signatures_completed: bool = False
    funding_completed: bool = False
    
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

# Form Templates Database - Initialize all required forms
def initialize_form_templates():
    """Initialize all required form templates for different states"""
    
    templates = {
        # PURCHASE AGREEMENT / BUYER'S ORDER
        FormType.PURCHASE_AGREEMENT: {
            "title": "Motor Vehicle Purchase Agreement",
            "description": "Main contract outlining vehicle sale details, pricing, fees, taxes, and financing",
            "fields": [
                {"name": "dealer_name", "type": "text", "required": True, "label": "Dealer Name"},
                {"name": "dealer_address", "type": "text", "required": True, "label": "Dealer Address"},
                {"name": "dealer_license", "type": "text", "required": True, "label": "Dealer License Number"},
                {"name": "customer_name", "type": "text", "required": True, "label": "Customer Full Name"},
                {"name": "customer_address", "type": "text", "required": True, "label": "Customer Address"},
                {"name": "customer_phone", "type": "text", "required": True, "label": "Customer Phone"},
                {"name": "vehicle_year", "type": "number", "required": True, "label": "Vehicle Year"},
                {"name": "vehicle_make", "type": "text", "required": True, "label": "Vehicle Make"},
                {"name": "vehicle_model", "type": "text", "required": True, "label": "Vehicle Model"},
                {"name": "vehicle_vin", "type": "text", "required": True, "label": "VIN"},
                {"name": "vehicle_mileage", "type": "number", "required": True, "label": "Odometer Reading"},
                {"name": "purchase_price", "type": "currency", "required": True, "label": "Purchase Price"},
                {"name": "trade_in_value", "type": "currency", "required": False, "label": "Trade-in Value"},
                {"name": "sales_tax", "type": "currency", "required": True, "label": "Sales Tax"},
                {"name": "title_fee", "type": "currency", "required": True, "label": "Title Fee"},
                {"name": "license_fee", "type": "currency", "required": True, "label": "License Fee"},
                {"name": "doc_fee", "type": "currency", "required": True, "label": "Documentation Fee"},
                {"name": "total_amount", "type": "currency", "required": True, "label": "Total Amount"},
                {"name": "financing", "type": "boolean", "required": True, "label": "Financing Required"},
                {"name": "delivery_date", "type": "date", "required": True, "label": "Delivery Date"}
            ]
        },
        
        # ODOMETER DISCLOSURE STATEMENT
        FormType.ODOMETER_DISCLOSURE: {
            "title": "Federal Odometer Disclosure Statement",
            "description": "Required federal disclosure of vehicle mileage at time of sale",
            "fields": [
                {"name": "transferor_name", "type": "text", "required": True, "label": "Transferor (Seller) Name"},
                {"name": "transferee_name", "type": "text", "required": True, "label": "Transferee (Buyer) Name"},
                {"name": "vehicle_year", "type": "number", "required": True, "label": "Vehicle Year"},
                {"name": "vehicle_make", "type": "text", "required": True, "label": "Vehicle Make"},
                {"name": "vehicle_model", "type": "text", "required": True, "label": "Vehicle Model"},
                {"name": "vehicle_vin", "type": "text", "required": True, "label": "VIN"},
                {"name": "odometer_reading", "type": "number", "required": True, "label": "Odometer Reading"},
                {"name": "odometer_status", "type": "select", "required": True, "label": "Odometer Status",
                 "options": ["Actual Mileage", "Not Actual Mileage", "Exceeds Mechanical Limits"]},
                {"name": "transfer_date", "type": "date", "required": True, "label": "Date of Transfer"},
                {"name": "transferor_signature", "type": "signature", "required": True, "label": "Transferor Signature"},
                {"name": "transferee_signature", "type": "signature", "required": True, "label": "Transferee Signature"}
            ]
        },
        
        # TRUTH IN LENDING DISCLOSURE (TILA)
        FormType.TRUTH_IN_LENDING: {
            "title": "Truth-in-Lending Disclosure Statement",
            "description": "Federal TILA disclosure of loan costs and terms",
            "fields": [
                {"name": "creditor_name", "type": "text", "required": True, "label": "Creditor Name"},
                {"name": "customer_name", "type": "text", "required": True, "label": "Customer Name"},
                {"name": "customer_address", "type": "text", "required": True, "label": "Customer Address"},
                {"name": "annual_percentage_rate", "type": "percentage", "required": True, "label": "Annual Percentage Rate (APR)"},
                {"name": "finance_charge", "type": "currency", "required": True, "label": "Finance Charge"},
                {"name": "amount_financed", "type": "currency", "required": True, "label": "Amount Financed"},
                {"name": "total_of_payments", "type": "currency", "required": True, "label": "Total of Payments"},
                {"name": "payment_schedule", "type": "text", "required": True, "label": "Payment Schedule"},
                {"name": "monthly_payment", "type": "currency", "required": True, "label": "Monthly Payment Amount"},
                {"name": "number_of_payments", "type": "number", "required": True, "label": "Number of Payments"},
                {"name": "first_payment_date", "type": "date", "required": True, "label": "First Payment Due Date"},
                {"name": "security_interest", "type": "text", "required": True, "label": "Security Interest Description"},
                {"name": "late_charge", "type": "currency", "required": False, "label": "Late Charge"},
                {"name": "prepayment_penalty", "type": "text", "required": False, "label": "Prepayment Penalty"}
            ]
        },
        
        # DAMAGE DISCLOSURE STATEMENT
        FormType.DAMAGE_DISCLOSURE: {
            "title": "Motor Vehicle Damage Disclosure Statement",
            "description": "Required disclosure of structural damage for used vehicles",
            "fields": [
                {"name": "dealer_name", "type": "text", "required": True, "label": "Dealer Name"},
                {"name": "customer_name", "type": "text", "required": True, "label": "Customer Name"},
                {"name": "vehicle_year", "type": "number", "required": True, "label": "Vehicle Year"},
                {"name": "vehicle_make", "type": "text", "required": True, "label": "Vehicle Make"},
                {"name": "vehicle_model", "type": "text", "required": True, "label": "Vehicle Model"},
                {"name": "vehicle_vin", "type": "text", "required": True, "label": "VIN"},
                {"name": "damage_disclosure", "type": "select", "required": True, "label": "Damage Disclosure",
                 "options": ["No Damage", "Minor Damage", "Structural Damage", "Unknown"]},
                {"name": "damage_description", "type": "textarea", "required": False, "label": "Damage Description"},
                {"name": "repair_description", "type": "textarea", "required": False, "label": "Repair Description"},
                {"name": "total_damage_cost", "type": "currency", "required": False, "label": "Total Damage/Repair Cost"},
                {"name": "disclosure_date", "type": "date", "required": True, "label": "Disclosure Date"}
            ]
        },
        
        # TRADE-IN APPRAISAL
        FormType.TRADE_IN_APPRAISAL: {
            "title": "Trade-In Vehicle Appraisal",
            "description": "Documentation of trade-in vehicle evaluation and value",
            "fields": [
                {"name": "trade_vehicle_year", "type": "number", "required": True, "label": "Trade Vehicle Year"},
                {"name": "trade_vehicle_make", "type": "text", "required": True, "label": "Trade Vehicle Make"},
                {"name": "trade_vehicle_model", "type": "text", "required": True, "label": "Trade Vehicle Model"},
                {"name": "trade_vehicle_vin", "type": "text", "required": True, "label": "Trade Vehicle VIN"},
                {"name": "trade_vehicle_mileage", "type": "number", "required": True, "label": "Trade Vehicle Mileage"},
                {"name": "trade_vehicle_condition", "type": "select", "required": True, "label": "Vehicle Condition",
                 "options": ["Excellent", "Good", "Fair", "Poor"]},
                {"name": "exterior_condition", "type": "textarea", "required": True, "label": "Exterior Condition Notes"},
                {"name": "interior_condition", "type": "textarea", "required": True, "label": "Interior Condition Notes"},
                {"name": "mechanical_condition", "type": "textarea", "required": True, "label": "Mechanical Condition Notes"},
                {"name": "book_value", "type": "currency", "required": True, "label": "Book Value"},
                {"name": "appraised_value", "type": "currency", "required": True, "label": "Appraised Value"},
                {"name": "trade_allowance", "type": "currency", "required": True, "label": "Trade Allowance"},
                {"name": "payoff_amount", "type": "currency", "required": False, "label": "Payoff Amount"},
                {"name": "net_trade_value", "type": "currency", "required": True, "label": "Net Trade Value"},
                {"name": "appraiser_name", "type": "text", "required": True, "label": "Appraiser Name"},
                {"name": "appraisal_date", "type": "date", "required": True, "label": "Appraisal Date"}
            ]
        },
        
        # EXTENDED WARRANTY CONTRACT
        FormType.EXTENDED_WARRANTY: {
            "title": "Extended Warranty Service Contract",
            "description": "Vehicle Service Contract for extended warranty coverage",
            "fields": [
                {"name": "contract_number", "type": "text", "required": True, "label": "Contract Number"},
                {"name": "customer_name", "type": "text", "required": True, "label": "Customer Name"},
                {"name": "customer_address", "type": "text", "required": True, "label": "Customer Address"},
                {"name": "vehicle_year", "type": "number", "required": True, "label": "Vehicle Year"},
                {"name": "vehicle_make", "type": "text", "required": True, "label": "Vehicle Make"},
                {"name": "vehicle_model", "type": "text", "required": True, "label": "Vehicle Model"},
                {"name": "vehicle_vin", "type": "text", "required": True, "label": "VIN"},
                {"name": "mileage_at_sale", "type": "number", "required": True, "label": "Mileage at Sale"},
                {"name": "coverage_type", "type": "select", "required": True, "label": "Coverage Type",
                 "options": ["Powertrain", "Bumper-to-Bumper", "Premium", "Named Component"]},
                {"name": "contract_term", "type": "select", "required": True, "label": "Contract Term",
                 "options": ["12 months", "24 months", "36 months", "48 months", "60 months"]},
                {"name": "mileage_limit", "type": "number", "required": True, "label": "Mileage Limit"},
                {"name": "contract_price", "type": "currency", "required": True, "label": "Contract Price"},
                {"name": "deductible", "type": "currency", "required": True, "label": "Deductible Amount"},
                {"name": "effective_date", "type": "date", "required": True, "label": "Effective Date"},
                {"name": "expiration_date", "type": "date", "required": True, "label": "Expiration Date"}
            ]
        }
    }
    
    return templates

# State-specific form requirements
def get_state_form_requirements(state_code: str):
    """Get required forms for specific state"""
    
    state_requirements = {
        "CA": {
            "required_forms": [
                FormType.PURCHASE_AGREEMENT,
                FormType.ODOMETER_DISCLOSURE,
                FormType.TRUTH_IN_LENDING,
                FormType.SMOG_CERTIFICATE,
                FormType.DAMAGE_DISCLOSURE
            ],
            "additional_fees": {
                "smog_fee": 20.00,
                "tire_fee": 1.75
            }
        },
        "TX": {
            "required_forms": [
                FormType.PURCHASE_AGREEMENT,
                FormType.ODOMETER_DISCLOSURE,
                FormType.TRUTH_IN_LENDING,
                FormType.SAFETY_INSPECTION
            ],
            "additional_fees": {
                "inspection_fee": 12.50
            }
        },
        "FL": {
            "required_forms": [
                FormType.PURCHASE_AGREEMENT,
                FormType.ODOMETER_DISCLOSURE,
                FormType.TRUTH_IN_LENDING,
                FormType.DAMAGE_DISCLOSURE
            ],
            "additional_fees": {}
        },
        "NY": {
            "required_forms": [
                FormType.PURCHASE_AGREEMENT,
                FormType.ODOMETER_DISCLOSURE,
                FormType.TRUTH_IN_LENDING,
                FormType.DAMAGE_DISCLOSURE,
                FormType.LEMON_LAW_DISCLOSURE
            ],
            "additional_fees": {
                "dmv_fee": 50.00
            }
        }
    }
    
    return state_requirements.get(state_code, state_requirements["CA"])  # Default to CA

# Document generation functions
def generate_purchase_agreement_pdf(deal_data: Dict) -> str:
    """Generate Purchase Agreement PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("MOTOR VEHICLE PURCHASE AGREEMENT", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Dealer Information
    dealer_info = f"""
    <b>DEALER INFORMATION:</b><br/>
    Dealer Name: {deal_data.get('dealer_name', 'ABC Motors')}<br/>
    Address: {deal_data.get('dealer_address', '123 Main St, City, State 12345')}<br/>
    License #: {deal_data.get('dealer_license', 'DL123456')}<br/>
    Phone: {deal_data.get('dealer_phone', '(555) 123-4567')}
    """
    story.append(Paragraph(dealer_info, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Customer Information
    customer = deal_data.get('customer', {})
    customer_info = f"""
    <b>PURCHASER INFORMATION:</b><br/>
    Name: {customer.get('first_name', '')} {customer.get('last_name', '')}<br/>
    Address: {customer.get('address', '')}<br/>
    City, State: {customer.get('city', '')}, {customer.get('state', '')}<br/>
    ZIP: {customer.get('zip_code', '')}<br/>
    Phone: {customer.get('phone', '')}
    """
    story.append(Paragraph(customer_info, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Vehicle Information
    vehicle = deal_data.get('vehicle', {})
    vehicle_info = f"""
    <b>VEHICLE INFORMATION:</b><br/>
    Year: {vehicle.get('year', '')}<br/>
    Make: {vehicle.get('make', '')}<br/>
    Model: {vehicle.get('model', '')}<br/>
    VIN: {vehicle.get('vin', '')}<br/>
    Mileage: {vehicle.get('mileage', 0):,}<br/>
    Condition: {vehicle.get('condition', '').title()}
    """
    story.append(Paragraph(vehicle_info, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Pricing Table
    pricing_data = [
        ['ITEM', 'AMOUNT'],
        ['Vehicle Price', f"${vehicle.get('selling_price', 0):,.2f}"],
        ['Trade-in Value', f"${deal_data.get('trade_in_value', 0):,.2f}"],
        ['Sales Tax', f"${deal_data.get('sales_tax', 0):,.2f}"],
        ['Title Fee', f"${deal_data.get('title_fee', 0):,.2f}"],
        ['License Fee', f"${deal_data.get('license_fee', 0):,.2f}"],
        ['Documentation Fee', f"${deal_data.get('doc_fee', 0):,.2f}"],
        ['TOTAL AMOUNT', f"${deal_data.get('total_deal_amount', 0):,.2f}"]
    ]
    
    pricing_table = Table(pricing_data, colWidths=[3*inch, 2*inch])
    pricing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    story.append(pricing_table)
    story.append(Spacer(1, 24))
    
    # Signature Section
    signature_section = """
    <b>SIGNATURES:</b><br/><br/>
    Customer Signature: _________________________________ Date: ___________<br/><br/>
    Print Name: _________________________________<br/><br/><br/>
    Dealer Representative: _________________________________ Date: ___________<br/><br/>
    Print Name: _________________________________
    """
    story.append(Paragraph(signature_section, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # Return base64 encoded PDF
    return base64.b64encode(pdf_bytes).decode('utf-8')
def generate_odometer_disclosure_pdf(deal_data: Dict) -> str:
    """Generate Odometer Disclosure Statement PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("FEDERAL ODOMETER DISCLOSURE STATEMENT", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Federal Warning
    warning = """
    <b>FEDERAL LAW REQUIRES THAT YOU STATE THE MILEAGE IN CONNECTION WITH THE TRANSFER OF OWNERSHIP. 
    FAILURE TO COMPLETE OR PROVIDING A FALSE STATEMENT MAY RESULT IN FINES AND/OR IMPRISONMENT.</b>
    """
    story.append(Paragraph(warning, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Vehicle Information
    vehicle = deal_data.get('vehicle', {})
    vehicle_info = f"""
    <b>VEHICLE IDENTIFICATION:</b><br/>
    Year: {vehicle.get('year', '')}<br/>
    Make: {vehicle.get('make', '')}<br/>
    Model: {vehicle.get('model', '')}<br/>
    Body Type: Sedan<br/>
    Vehicle Identification Number: {vehicle.get('vin', '')}
    """
    story.append(Paragraph(vehicle_info, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Odometer Reading
    odometer_info = f"""
    <b>ODOMETER DISCLOSURE:</b><br/>
    I state that the odometer now reads: <b>{vehicle.get('mileage', 0):,} miles</b><br/><br/>
    (Check one box only):<br/>
    ☑ I hereby certify that to the best of my knowledge the odometer reading reflects the actual mileage of the vehicle.<br/>
    ☐ I hereby certify that to the best of my knowledge the odometer reading reflects the amount of mileage in excess of its mechanical limits.<br/>
    ☐ I hereby certify that to the best of my knowledge the odometer reading is NOT the actual mileage.
    """
    story.append(Paragraph(odometer_info, styles['Normal']))
    story.append(Spacer(1, 24))
    
    # Signature blocks
    signature_section = """
    <b>TRANSFEROR (SELLER):</b><br/><br/>
    Signature: _________________________________ Date: ___________<br/><br/>
    Print Name: _________________________________<br/><br/>
    <b>TRANSFEREE (BUYER):</b><br/><br/>
    Signature: _________________________________ Date: ___________<br/><br/>
    Print Name: _________________________________
    """
    story.append(Paragraph(signature_section, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return base64.b64encode(pdf_bytes).decode('utf-8')

def generate_truth_in_lending_pdf(deal_data: Dict) -> str:
    """Generate Truth-in-Lending Disclosure PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("TRUTH-IN-LENDING DISCLOSURE STATEMENT", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Creditor Information
    creditor_info = """
    <b>CREDITOR:</b> ABC Motors Finance<br/>
    <b>ADDRESS:</b> 123 Main Street, City, State 12345
    """
    story.append(Paragraph(creditor_info, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Customer Information
    customer = deal_data.get('customer', {})
    customer_info = f"""
    <b>CUSTOMER:</b> {customer.get('first_name', '')} {customer.get('last_name', '')}<br/>
    <b>ADDRESS:</b> {customer.get('address', '')}, {customer.get('city', '')}, {customer.get('state', '')} {customer.get('zip_code', '')}
    """
    story.append(Paragraph(customer_info, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Finance terms
    finance_terms = deal_data.get('finance_terms', {})
    
    # TILA Box
    tila_data = [
        ['ANNUAL PERCENTAGE RATE', 'FINANCE CHARGE', 'AMOUNT FINANCED', 'TOTAL OF PAYMENTS'],
        [f"{finance_terms.get('apr', 0)}%", f"${finance_terms.get('total_interest', 0):,.2f}", 
         f"${finance_terms.get('loan_amount', 0):,.2f}", f"${finance_terms.get('total_cost', 0):,.2f}"],
        ['The cost of your credit as a yearly rate', 'The dollar amount the credit will cost you', 
         'The amount of credit provided to you', 'The amount you will have paid after making all payments']
    ]
    
    tila_table = Table(tila_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    tila_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(tila_table)
    story.append(Spacer(1, 12))
    
    # Payment schedule
    payment_info = f"""
    <b>PAYMENT SCHEDULE:</b><br/>
    Number of Payments: {finance_terms.get('term_months', 0)}<br/>
    Amount of Payments: ${finance_terms.get('monthly_payment', 0):,.2f}<br/>
    When Payments are Due: Monthly beginning 30 days from date of this contract
    """
    story.append(Paragraph(payment_info, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Security interest
    vehicle = deal_data.get('vehicle', {})
    security_info = f"""
    <b>SECURITY:</b> You are giving a security interest in the {vehicle.get('year', '')} {vehicle.get('make', '')} {vehicle.get('model', '')} being purchased.
    """
    story.append(Paragraph(security_info, styles['Normal']))
    story.append(Spacer(1, 24))
    
    # Signature
    signature_section = """
    <b>ACKNOWLEDGMENT:</b><br/>
    I acknowledge receipt of a copy of this disclosure statement.<br/><br/>
    Customer Signature: _________________________________ Date: ___________
    """
    story.append(Paragraph(signature_section, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return base64.b64encode(pdf_bytes).decode('utf-8')

def generate_bill_of_sale_pdf(deal_data: Dict) -> str:
    """Generate Bill of Sale PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("MOTOR VEHICLE BILL OF SALE", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Transaction details
    customer = deal_data.get('customer', {})
    vehicle = deal_data.get('vehicle', {})
    
    transaction_info = f"""
    <b>SELLER:</b> ABC Motors<br/>
    Address: 123 Main Street, City, State 12345<br/><br/>
    
    <b>BUYER:</b> {customer.get('first_name', '')} {customer.get('last_name', '')}<br/>
    Address: {customer.get('address', '')}, {customer.get('city', '')}, {customer.get('state', '')} {customer.get('zip_code', '')}<br/><br/>
    
    <b>VEHICLE DESCRIPTION:</b><br/>
    Year: {vehicle.get('year', '')}<br/>
    Make: {vehicle.get('make', '')}<br/>
    Model: {vehicle.get('model', '')}<br/>
    VIN: {vehicle.get('vin', '')}<br/>
    Odometer: {vehicle.get('mileage', 0):,} miles<br/><br/>
    
    <b>PURCHASE PRICE:</b> ${vehicle.get('selling_price', 0):,.2f}<br/>
    <b>DATE OF SALE:</b> {datetime.utcnow().strftime('%B %d, %Y')}
    """
    story.append(Paragraph(transaction_info, styles['Normal']))
    story.append(Spacer(1, 24))
    
    # Legal text
    legal_text = """
    The seller hereby sells, transfers and conveys to the buyer the above described motor vehicle. 
    The seller warrants that they have good and marketable title to said vehicle, free and clear of all liens and encumbrances.
    """
    story.append(Paragraph(legal_text, styles['Normal']))
    story.append(Spacer(1, 24))
    
    # Signatures
    signature_section = """
    <b>SELLER:</b><br/><br/>
    Signature: _________________________________ Date: ___________<br/>
    Print Name: ABC Motors Representative<br/><br/>
    
    <b>BUYER:</b><br/><br/>
    Signature: _________________________________ Date: ___________<br/>
    Print Name: {customer.get('first_name', '')} {customer.get('last_name', '')}
    """.format(customer=customer)
    story.append(Paragraph(signature_section, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return base64.b64encode(pdf_bytes).decode('utf-8')
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


# Forms Management Endpoints
@api_router.get("/forms/templates", response_model=List[dict])
async def get_form_templates(state: str = "CA"):
    """Get all form templates for a specific state"""
    templates = initialize_form_templates()
    state_requirements = get_state_form_requirements(state)
    
    # Filter templates based on state requirements
    filtered_templates = {}
    for form_type in state_requirements["required_forms"]:
        if form_type in templates:
            filtered_templates[form_type.value] = {
                "form_type": form_type.value,
                "title": templates[form_type]["title"],
                "description": templates[form_type]["description"],
                "fields": templates[form_type]["fields"],
                "required": True
            }
    
    return list(filtered_templates.values())

@api_router.get("/forms/requirements/{state}")
async def get_state_requirements(state: str):
    """Get form requirements for a specific state"""
    return get_state_form_requirements(state)

@api_router.post("/deals/{deal_id}/forms")
async def create_deal_form(deal_id: str, form_data: dict):
    """Create a form for a deal"""
    try:
        # Get deal
        deal = await db.deals.find_one({"id": deal_id})
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        
        # Create form
        form = FormData(
            deal_id=deal_id,
            form_template_id=form_data.get("template_id"),
            form_type=FormType(form_data.get("form_type")),
            field_values=form_data.get("field_values", {}),
            status=FormStatus.DRAFT
        )
        
        # Save form
        await db.forms.insert_one(form.dict())
        
        # Update deal with form ID
        await db.deals.update_one(
            {"id": deal_id},
            {"$addToSet": {"forms": form.id}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        return form
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/deals/{deal_id}/forms")
async def get_deal_forms(deal_id: str):
    """Get all forms for a deal"""
    forms = await db.forms.find({"deal_id": deal_id}).to_list(100)
    return [FormData(**form) for form in forms]

@api_router.put("/forms/{form_id}")
async def update_form(form_id: str, form_data: dict):
    """Update form data"""
    try:
        update_data = {
            "field_values": form_data.get("field_values", {}),
            "status": form_data.get("status", FormStatus.DRAFT),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.forms.update_one({"id": form_id}, {"$set": update_data})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Form not found")
        
        return {"message": "Form updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Document Generation Endpoints
class DocumentGenerationRequest(BaseModel):
    document_types: List[str]

@api_router.post("/deals/{deal_id}/documents/generate")
async def generate_deal_documents(deal_id: str, request: DocumentGenerationRequest):
    """Generate documents for a deal"""
    try:
        # Get deal data
        deal = await db.deals.find_one({"id": deal_id})
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        
        # Convert MongoDB document to dict and handle ObjectId
        deal_dict = {}
        for key, value in deal.items():
            if key == '_id':
                continue
            deal_dict[key] = value
        
        generated_docs = []
        
        for doc_type in request.document_types:
            pdf_content = None
            title = ""
            
            if doc_type == "purchase_agreement":
                pdf_content = generate_purchase_agreement_pdf(deal_dict)
                title = "Motor Vehicle Purchase Agreement"
            elif doc_type == "odometer_disclosure":
                pdf_content = generate_odometer_disclosure_pdf(deal_dict)
                title = "Federal Odometer Disclosure Statement"
            elif doc_type == "truth_in_lending":
                pdf_content = generate_truth_in_lending_pdf(deal_dict)
                title = "Truth-in-Lending Disclosure Statement"
            elif doc_type == "bill_of_sale":
                pdf_content = generate_bill_of_sale_pdf(deal_dict)
                title = "Motor Vehicle Bill of Sale"
            else:
                # Default document
                pdf_content = generate_purchase_agreement_pdf(deal_dict)
                title = f"{doc_type.replace('_', ' ').title()}"
            
            doc = GeneratedDocument(
                deal_id=deal_id,
                template_id=f"{doc_type}_template",
                document_type=doc_type,
                title=title,
                generated_content=f"<p>{title} Generated</p>",
                pdf_content=pdf_content,
                variables_used=deal,
                status=DocumentStatus.GENERATED,
                signature_required=True
            )
            
            await db.documents.insert_one(doc.dict())
            generated_docs.append(doc)
        
        # Update deal
        doc_ids = [doc.id for doc in generated_docs]
        await db.deals.update_one(
            {"id": deal_id},
            {"$addToSet": {"documents": {"$each": doc_ids}}, "$set": {"docs_generated": True, "updated_at": datetime.utcnow()}}
        )
        
        return {"message": f"Generated {len(generated_docs)} documents", "documents": generated_docs}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/deals/{deal_id}/documents")
async def get_deal_documents(deal_id: str):
    """Get all documents for a deal"""
    documents = await db.documents.find({"deal_id": deal_id}).to_list(100)
    return [GeneratedDocument(**doc) for doc in documents]

@api_router.get("/documents/{document_id}/pdf")
async def get_document_pdf(document_id: str):
    """Get PDF content of a document"""
    document = await db.documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not document.get("pdf_content"):
        raise HTTPException(status_code=400, detail="PDF not available for this document")
    
    return {"pdf_content": document["pdf_content"]}

# Credit Application & Bank Integration Endpoints
@api_router.post("/deals/{deal_id}/credit-application")
async def create_credit_application(deal_id: str, credit_data: dict):
    """Create a credit application for a deal"""
    try:
        deal = await db.deals.find_one({"id": deal_id})
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        
        credit_app = CreditApplication(
            deal_id=deal_id,
            customer_id=deal["customer"]["id"] if "id" in deal["customer"] else str(uuid.uuid4()),
            **credit_data
        )
        
        await db.credit_applications.insert_one(credit_app.dict())
        
        # Update deal
        await db.deals.update_one(
            {"id": deal_id},
            {"$addToSet": {"credit_applications": credit_app.id}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        return credit_app
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/lenders")
async def get_lenders():
    """Get all available lenders"""
    # Mock lender data - in production, this would be from database
    lenders = [
        {
            "id": "chase_auto",
            "name": "Chase Auto Finance",
            "code": "CHASE",
            "is_active": True,
            "min_credit_score": 620,
            "max_ltv": 0.9,
            "interest_rates": {"36": 4.99, "48": 5.49, "60": 5.99, "72": 6.49},
            "specialties": ["prime", "luxury"]
        },
        {
            "id": "wells_fargo",
            "name": "Wells Fargo Auto",
            "code": "WF",
            "is_active": True,
            "min_credit_score": 650,
            "max_ltv": 0.85,
            "interest_rates": {"36": 4.75, "48": 5.25, "60": 5.75, "72": 6.25},
            "specialties": ["prime"]
        },
        {
            "id": "capital_one",
            "name": "Capital One Auto Finance",
            "code": "COF",
            "is_active": True,
            "min_credit_score": 580,
            "max_ltv": 0.95,
            "interest_rates": {"36": 6.99, "48": 7.49, "60": 7.99, "72": 8.49},
            "specialties": ["subprime", "near_prime"]
        },
        {
            "id": "santander",
            "name": "Santander Consumer USA",
            "code": "SC",
            "is_active": True,
            "min_credit_score": 500,
            "max_ltv": 1.0,
            "interest_rates": {"36": 8.99, "48": 9.99, "60": 11.99, "72": 13.99},
            "specialties": ["subprime", "deep_subprime"]
        }
    ]
    
    return lenders

@api_router.post("/deals/{deal_id}/submit-to-lenders")
async def submit_to_lenders(deal_id: str, submission_data: dict):
    """Submit credit application to multiple lenders"""
    try:
        # Get deal and credit application
        deal = await db.deals.find_one({"id": deal_id})
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        
        credit_apps = await db.credit_applications.find({"deal_id": deal_id}).to_list(10)
        if not credit_apps:
            raise HTTPException(status_code=400, detail="No credit application found for deal")
        
        credit_app = credit_apps[0]  # Use first credit application
        selected_lenders = submission_data.get("lender_ids", [])
        
        submissions = []
        
        for lender_id in selected_lenders:
            # Create lender submission
            submission = LenderSubmission(
                deal_id=deal_id,
                credit_application_id=credit_app["id"],
                lender_id=lender_id,
                submitted_data={
                    "customer": deal["customer"],
                    "vehicle": deal["vehicle"],
                    "credit_info": credit_app,
                    "loan_request": {
                        "amount": submission_data.get("loan_amount", deal["total_deal_amount"]),
                        "term": submission_data.get("loan_term", 60)
                    }
                },
                status=LenderStatus.SUBMITTED
            )
            
            await db.lender_submissions.insert_one(submission.dict())
            submissions.append(submission)
            
            # Simulate lender response (in production, this would be API calls)
            await simulate_lender_response(submission.id, lender_id, credit_app)
        
        # Update deal
        submission_ids = [sub.id for sub in submissions]
        await db.deals.update_one(
            {"id": deal_id},
            {"$addToSet": {"lender_submissions": {"$each": submission_ids}}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        return {"message": f"Submitted to {len(submissions)} lenders", "submissions": submissions}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/deals/{deal_id}/lender-responses")
async def get_lender_responses(deal_id: str):
    """Get all lender responses for a deal"""
    submissions = await db.lender_submissions.find({"deal_id": deal_id}).to_list(100)
    return [LenderSubmission(**sub) for sub in submissions]

async def simulate_lender_response(submission_id: str, lender_id: str, credit_app: dict):
    """Simulate lender response based on credit profile"""
    # Simple simulation based on credit score
    credit_score = credit_app.get("customer", {}).get("credit_score", 650)
    
    # Determine approval likelihood
    if credit_score >= 720:
        decision = "approved"
        rate_adjustment = 0.0
    elif credit_score >= 650:
        decision = "approved"
        rate_adjustment = 1.0
    elif credit_score >= 600:
        decision = "conditional"
        rate_adjustment = 2.0
    else:
        decision = "approved" if lender_id in ["santander", "capital_one"] else "declined"
        rate_adjustment = 3.0
    
    # Update submission with response
    if decision == "approved":
        update_data = {
            "status": LenderStatus.APPROVED,
            "decision": "approved",
            "approved_amount": credit_app.get("requested_amount", 25000),
            "approved_rate": 5.99 + rate_adjustment,
            "approved_term": credit_app.get("requested_term", 60),
            "responded_at": datetime.utcnow()
        }
    elif decision == "conditional":
        update_data = {
            "status": LenderStatus.CONDITIONAL,
            "decision": "conditional",
            "approved_amount": credit_app.get("requested_amount", 25000) * 0.9,
            "approved_rate": 7.99 + rate_adjustment,
            "approved_term": credit_app.get("requested_term", 60),
            "stipulations": ["Proof of Income", "Verification of Employment"],
            "responded_at": datetime.utcnow()
        }
    else:
        update_data = {
            "status": LenderStatus.DECLINED,
            "decision": "declined",
            "decline_reason": "Credit score below minimum requirements",
            "responded_at": datetime.utcnow()
        }
    
    await db.lender_submissions.update_one({"id": submission_id}, {"$set": update_data})

# E-Signature Endpoints
@api_router.post("/documents/{document_id}/signature-request")
async def create_signature_request(document_id: str, signature_data: dict):
    """Create a signature request for a document"""
    try:
        document = await db.documents.find_one({"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        signature_request = SignatureRequest(
            document_id=document_id,
            deal_id=document["deal_id"],
            signers=signature_data.get("signers", []),
            signing_order=signature_data.get("signing_order", []),
            expires_at=signature_data.get("expires_at")
        )
        
        await db.signature_requests.insert_one(signature_request.dict())
        
        # Update document status
        await db.documents.update_one(
            {"id": document_id},
            {"$set": {"status": DocumentStatus.SENT_FOR_SIGNATURE, "updated_at": datetime.utcnow()}}
        )
        
        return signature_request
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/signature-requests/{request_id}/sign")
async def sign_document(request_id: str, signature_data: dict):
    """Add a signature to a document"""
    try:
        signature_request = await db.signature_requests.find_one({"id": request_id})
        if not signature_request:
            raise HTTPException(status_code=404, detail="Signature request not found")
        
        signature = Signature(
            signature_request_id=request_id,
            document_id=signature_request["document_id"],
            signer_email=signature_data.get("signer_email"),
            signer_name=signature_data.get("signer_name"),
            signature_data=signature_data.get("signature_data"),
            ip_address=signature_data.get("ip_address"),
            user_agent=signature_data.get("user_agent"),
            signed_at=datetime.utcnow(),
            legal_notice_acknowledged=signature_data.get("legal_notice_acknowledged", False)
        )
        
        await db.signatures.insert_one(signature.dict())
        
        # Check if all signatures are complete
        all_signatures = await db.signatures.find({"signature_request_id": request_id}).to_list(100)
        required_signers = len(signature_request["signers"])
        
        if len(all_signatures) >= required_signers:
            # All signatures complete
            await db.signature_requests.update_one(
                {"id": request_id},
                {"$set": {"status": "completed", "completed_at": datetime.utcnow()}}
            )
            
            # Update document status
            await db.documents.update_one(
                {"id": signature_request["document_id"]},
                {"$set": {"status": DocumentStatus.SIGNED, "updated_at": datetime.utcnow()}}
            )
        
        return signature
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/deals/{deal_id}/signature-status")
async def get_deal_signature_status(deal_id: str):
    """Get signature status for all documents in a deal"""
    documents = await db.documents.find({"deal_id": deal_id}).to_list(100)
    signature_requests = await db.signature_requests.find({"deal_id": deal_id}).to_list(100)
    
    status = {
        "total_documents": len(documents),
        "documents_requiring_signature": sum(1 for doc in documents if doc.get("signature_required", False)),
        "documents_signed": sum(1 for doc in documents if doc.get("status") == DocumentStatus.SIGNED),
        "signature_requests": signature_requests
    }
    
    return status


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
