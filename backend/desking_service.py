"""
Advanced Desking Tool Service for Pulse Auto Market
Handles payment calculations, F&I products, and deal structuring
"""
import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP

from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

class DealType(str, Enum):
    CASH = "cash"
    FINANCE = "finance"
    LEASE = "lease"

class PaymentFrequency(str, Enum):
    MONTHLY = "monthly"
    BIWEEKLY = "biweekly"
    WEEKLY = "weekly"

class FIProduct(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str  # "warranty", "insurance", "protection"
    base_cost: float
    markup_percentage: float
    dealer_cost: float
    customer_price: float
    term_months: Optional[int] = None
    coverage_details: str = ""

class TradeIn(BaseModel):
    make: str
    model: str
    year: int
    mileage: int
    condition: str  # "excellent", "good", "fair", "poor"
    estimated_value: float
    payoff_amount: float = 0.0
    net_trade_value: float = 0.0

class TaxInfo(BaseModel):
    state: str
    county: str = ""
    city: str = ""
    zip_code: str
    tax_rate: float
    doc_fee: float
    title_fee: float = 0.0
    registration_fee: float = 0.0

class FinanceTerms(BaseModel):
    loan_amount: float
    interest_rate: float
    term_months: int
    down_payment: float = 0.0
    payment_frequency: PaymentFrequency = PaymentFrequency.MONTHLY
    first_payment_date: Optional[str] = None

class LeaseTerms(BaseModel):
    msrp: float
    cap_cost: float
    residual_percentage: float
    money_factor: float
    term_months: int
    down_payment: float = 0.0
    annual_mileage: int = 12000
    acquisition_fee: float = 595.0
    disposition_fee: float = 350.0

class DealCalculation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dealer_id: str
    vehicle_vin: str
    customer_name: str = ""
    deal_type: DealType
    
    # Vehicle pricing
    vehicle_price: float
    trade_in: Optional[TradeIn] = None
    rebates: float = 0.0
    dealer_discount: float = 0.0
    
    # Finance/Lease terms
    finance_terms: Optional[FinanceTerms] = None
    lease_terms: Optional[LeaseTerms] = None
    
    # F&I Products
    fi_products: List[FIProduct] = []
    
    # Tax information
    tax_info: TaxInfo
    
    # Calculated results
    monthly_payment: float = 0.0
    total_amount_financed: float = 0.0
    total_cost: float = 0.0
    dealer_profit: float = 0.0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = ""
    notes: str = ""

class PaymentGrid(BaseModel):
    """Payment grid showing different term/rate combinations"""
    vehicle_price: float
    down_payment: float
    trade_value: float
    amount_financed: float
    grid: Dict[str, Dict[str, float]]  # term -> rate -> payment

class DeskingService:
    """Advanced desking and payment calculation service"""
    
    def __init__(self, db):
        self.db = db
        self.default_vsc_markup = float(os.getenv('DEFAULT_VSC_MARKUP', 30))
        self.default_gap_markup = float(os.getenv('DEFAULT_GAP_MARKUP', 25))
        self.default_doc_fee = float(os.getenv('DEFAULT_DOC_FEE', 199))
    
    def calculate_finance_payment(self, principal: float, rate: float, months: int, 
                                frequency: PaymentFrequency = PaymentFrequency.MONTHLY) -> float:
        """Calculate loan payment using standard amortization formula"""
        if rate == 0:
            return principal / months
        
        # Convert annual rate to period rate
        periods_per_year = {
            PaymentFrequency.MONTHLY: 12,
            PaymentFrequency.BIWEEKLY: 26,
            PaymentFrequency.WEEKLY: 52
        }
        
        period_rate = rate / 100 / periods_per_year[frequency]
        total_periods = months * (periods_per_year[frequency] / 12)
        
        # Payment calculation: P * [r(1+r)^n] / [(1+r)^n - 1]
        if period_rate > 0:
            payment = principal * (period_rate * (1 + period_rate) ** total_periods) / \
                     ((1 + period_rate) ** total_periods - 1)
        else:
            payment = principal / total_periods
        
        return round(payment, 2)
    
    def calculate_lease_payment(self, lease_terms: LeaseTerms) -> Tuple[float, Dict]:
        """Calculate lease payment and details"""
        # Adjusted cap cost (after down payment and trade)
        adjusted_cap_cost = lease_terms.cap_cost - lease_terms.down_payment
        
        # Residual value
        residual_value = lease_terms.msrp * (lease_terms.residual_percentage / 100)
        
        # Depreciation amount
        depreciation = adjusted_cap_cost - residual_value
        
        # Monthly depreciation
        monthly_depreciation = depreciation / lease_terms.term_months
        
        # Monthly finance charge (rent charge)
        monthly_finance = (adjusted_cap_cost + residual_value) * lease_terms.money_factor
        
        # Base monthly payment
        base_payment = monthly_depreciation + monthly_finance
        
        # Add acquisition fee (usually rolled into cap cost)
        total_monthly = base_payment
        
        details = {
            "adjusted_cap_cost": adjusted_cap_cost,
            "residual_value": residual_value,
            "depreciation": depreciation,
            "monthly_depreciation": monthly_depreciation,
            "monthly_finance": monthly_finance,
            "acquisition_fee": lease_terms.acquisition_fee,
            "disposition_fee": lease_terms.disposition_fee
        }
        
        return round(total_monthly, 2), details
    
    def calculate_tax_amount(self, taxable_amount: float, tax_info: TaxInfo) -> float:
        """Calculate tax on taxable amount"""
        return round(taxable_amount * (tax_info.tax_rate / 100), 2)
    
    def create_fi_product_menu(self, dealer_id: str, vehicle_price: float, term_months: int) -> List[FIProduct]:
        """Create F&I product menu with dealer-specific pricing"""
        products = []
        
        # Vehicle Service Contract (VSC/Warranty)
        vsc_base_cost = self._calculate_vsc_cost(vehicle_price, term_months)
        vsc_markup = self.default_vsc_markup
        vsc_dealer_cost = vsc_base_cost
        vsc_customer_price = vsc_base_cost * (1 + vsc_markup / 100)
        
        vsc = FIProduct(
            name="Extended Vehicle Service Contract",
            category="warranty",
            base_cost=vsc_base_cost,
            markup_percentage=vsc_markup,
            dealer_cost=vsc_dealer_cost,
            customer_price=vsc_customer_price,
            term_months=term_months,
            coverage_details=f"Comprehensive coverage for {term_months} months or 100,000 miles"
        )
        products.append(vsc)
        
        # GAP Insurance
        gap_base_cost = self._calculate_gap_cost(vehicle_price)
        gap_markup = self.default_gap_markup
        gap_dealer_cost = gap_base_cost
        gap_customer_price = gap_base_cost * (1 + gap_markup / 100)
        
        gap = FIProduct(
            name="Guaranteed Asset Protection (GAP)",
            category="insurance",
            base_cost=gap_base_cost,
            markup_percentage=gap_markup,
            dealer_cost=gap_dealer_cost,
            customer_price=gap_customer_price,
            coverage_details="Covers difference between loan balance and insurance payout"
        )
        products.append(gap)
        
        # Paint Protection
        paint_protection = FIProduct(
            name="Paint Protection Package",
            category="protection",
            base_cost=300.0,
            markup_percentage=100.0,
            dealer_cost=300.0,
            customer_price=600.0,
            coverage_details="Ceramic coating and paint protection film"
        )
        products.append(paint_protection)
        
        return products
    
    def _calculate_vsc_cost(self, vehicle_price: float, term_months: int) -> float:
        """Calculate VSC base cost based on vehicle price and term"""
        # Simple pricing model - in reality this would use actual provider rates
        base_rate = 0.08  # 8% of vehicle price
        term_multiplier = 1.0 + (term_months - 36) / 120  # Adjust for term length
        
        return round(vehicle_price * base_rate * term_multiplier, 2)
    
    def _calculate_gap_cost(self, vehicle_price: float) -> float:
        """Calculate GAP insurance cost"""
        # Typical GAP pricing model
        if vehicle_price < 25000:
            return 695.0
        elif vehicle_price < 50000:
            return 895.0
        else:
            return 1095.0
    
    async def calculate_deal(self, deal_data: Dict) -> DealCalculation:
        """Calculate complete deal with all components"""
        try:
            deal = DealCalculation(**deal_data)
            
            # Calculate net trade value
            if deal.trade_in:
                deal.trade_in.net_trade_value = max(0, 
                    deal.trade_in.estimated_value - deal.trade_in.payoff_amount)
            
            # Calculate adjusted selling price
            adjusted_price = deal.vehicle_price - deal.dealer_discount - deal.rebates
            if deal.trade_in:
                adjusted_price -= deal.trade_in.net_trade_value
            
            # Add F&I products
            fi_total = sum(product.customer_price for product in deal.fi_products)
            adjusted_price += fi_total
            
            # Add taxes and fees
            tax_amount = self.calculate_tax_amount(adjusted_price, deal.tax_info)
            total_with_tax = adjusted_price + tax_amount + deal.tax_info.doc_fee
            
            if deal.deal_type == DealType.CASH:
                deal.total_cost = total_with_tax
                deal.monthly_payment = 0.0
                
            elif deal.deal_type == DealType.FINANCE and deal.finance_terms:
                # Calculate amount to finance
                amount_financed = total_with_tax - deal.finance_terms.down_payment
                deal.total_amount_financed = amount_financed
                
                # Calculate monthly payment
                deal.monthly_payment = self.calculate_finance_payment(
                    amount_financed,
                    deal.finance_terms.interest_rate,
                    deal.finance_terms.term_months,
                    deal.finance_terms.payment_frequency
                )
                
                # Calculate total cost
                payments_per_year = {
                    PaymentFrequency.MONTHLY: 12,
                    PaymentFrequency.BIWEEKLY: 26,
                    PaymentFrequency.WEEKLY: 52
                }
                total_payments = deal.finance_terms.term_months * (
                    payments_per_year[deal.finance_terms.payment_frequency] / 12
                )
                deal.total_cost = (deal.monthly_payment * total_payments) + \
                                deal.finance_terms.down_payment
                
            elif deal.deal_type == DealType.LEASE and deal.lease_terms:
                # Calculate lease payment
                lease_payment, lease_details = self.calculate_lease_payment(deal.lease_terms)
                deal.monthly_payment = lease_payment
                
                # Calculate total lease cost
                deal.total_cost = (lease_payment * deal.lease_terms.term_months) + \
                                deal.lease_terms.down_payment + \
                                deal.lease_terms.acquisition_fee
            
            # Calculate dealer profit
            deal.dealer_profit = self._calculate_dealer_profit(deal)
            
            # Store deal in database
            await self.db.deals.insert_one(deal.dict())
            
            return deal
            
        except Exception as e:
            logger.error(f"Error calculating deal: {str(e)}")
            raise
    
    def _calculate_dealer_profit(self, deal: DealCalculation) -> float:
        """Calculate total dealer profit from the deal"""
        profit = 0.0
        
        # Front-end profit (discount given vs. markup available)
        # This would typically be: invoice_price - actual_cost + holdback
        # For now, using a simplified model
        front_end = deal.dealer_discount * -1  # Negative discount = profit
        
        # F&I profit
        fi_profit = sum(
            product.customer_price - product.dealer_cost 
            for product in deal.fi_products
        )
        
        # Finance reserve (if applicable)
        finance_reserve = 0.0
        if deal.deal_type == DealType.FINANCE and deal.finance_terms:
            # Typical reserve is 1-2% of loan amount
            finance_reserve = deal.total_amount_financed * 0.015  # 1.5%
        
        total_profit = front_end + fi_profit + finance_reserve
        return round(total_profit, 2)
    
    async def generate_payment_grid(self, vehicle_price: float, down_payment: float = 0.0,
                                  trade_value: float = 0.0, tax_rate: float = 8.25) -> PaymentGrid:
        """Generate payment grid with multiple term/rate combinations"""
        
        # Calculate amount to finance
        taxable_amount = vehicle_price - trade_value
        tax_amount = taxable_amount * (tax_rate / 100)
        total_amount = vehicle_price + tax_amount + self.default_doc_fee - trade_value
        amount_financed = total_amount - down_payment
        
        # Define term and rate ranges
        terms = [36, 48, 60, 72, 84]  # months
        rates = [3.99, 4.99, 5.99, 6.99, 7.99, 8.99]  # APR
        
        grid = {}
        
        for term in terms:
            grid[str(term)] = {}
            for rate in rates:
                payment = self.calculate_finance_payment(amount_financed, rate, term)
                grid[str(term)][str(rate)] = payment
        
        return PaymentGrid(
            vehicle_price=vehicle_price,
            down_payment=down_payment,
            trade_value=trade_value,
            amount_financed=amount_financed,
            grid=grid
        )
    
    async def get_dealer_deals(self, dealer_id: str, limit: int = 50) -> List[DealCalculation]:
        """Get recent deals for a dealer"""
        try:
            deals_data = await self.db.deals.find(
                {"dealer_id": dealer_id}
            ).sort("created_at", -1).limit(limit).to_list(limit)
            
            return [DealCalculation(**deal) for deal in deals_data]
            
        except Exception as e:
            logger.error(f"Error getting dealer deals: {str(e)}")
            return []
    
    async def get_deal_by_id(self, deal_id: str) -> Optional[DealCalculation]:
        """Get specific deal by ID"""
        try:
            deal_data = await self.db.deals.find_one({"id": deal_id})
            if deal_data:
                return DealCalculation(**deal_data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting deal {deal_id}: {str(e)}")
            return None
    
    async def update_deal(self, deal_id: str, updates: Dict) -> bool:
        """Update an existing deal"""
        try:
            result = await self.db.deals.update_one(
                {"id": deal_id},
                {"$set": updates}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating deal {deal_id}: {str(e)}")
            return False
    
    async def get_dealer_fi_stats(self, dealer_id: str) -> Dict:
        """Get F&I statistics for a dealer"""
        try:
            # Get deals with F&I products
            pipeline = [
                {"$match": {"dealer_id": dealer_id}},
                {"$unwind": "$fi_products"},
                {"$group": {
                    "_id": "$fi_products.category",
                    "count": {"$sum": 1},
                    "total_revenue": {"$sum": "$fi_products.customer_price"},
                    "total_profit": {"$sum": {"$subtract": ["$fi_products.customer_price", "$fi_products.dealer_cost"]}}
                }}
            ]
            
            fi_stats = await self.db.deals.aggregate(pipeline).to_list(10)
            
            # Calculate penetration rates
            total_deals = await self.db.deals.count_documents({"dealer_id": dealer_id})
            
            # Get average deal profit
            profit_pipeline = [
                {"$match": {"dealer_id": dealer_id}},
                {"$group": {
                    "_id": None,
                    "avg_profit": {"$avg": "$dealer_profit"},
                    "total_profit": {"$sum": "$dealer_profit"}
                }}
            ]
            
            profit_stats = await self.db.deals.aggregate(profit_pipeline).to_list(1)
            avg_profit = profit_stats[0]["avg_profit"] if profit_stats else 0
            total_profit = profit_stats[0]["total_profit"] if profit_stats else 0
            
            return {
                "total_deals": total_deals,
                "fi_product_stats": {item["_id"]: {
                    "count": item["count"],
                    "revenue": item["total_revenue"],
                    "profit": item["total_profit"],
                    "penetration_rate": round((item["count"] / total_deals * 100) if total_deals > 0 else 0, 1)
                } for item in fi_stats},
                "average_deal_profit": round(avg_profit, 2),
                "total_profit": round(total_profit, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting F&I stats for dealer {dealer_id}: {str(e)}")
            return {}
    
    async def create_deal_proposal(self, deal_id: str) -> Dict:
        """Create a formatted deal proposal for customer presentation"""
        try:
            deal = await self.get_deal_by_id(deal_id)
            if not deal:
                return {}
            
            # Get vehicle information
            vehicle = await self.db.vehicles.find_one({"vin": deal.vehicle_vin})
            
            proposal = {
                "deal_id": deal.id,
                "created_date": deal.created_at.strftime("%B %d, %Y"),
                "customer_name": deal.customer_name,
                "vehicle": {
                    "year": vehicle.get("year") if vehicle else "",
                    "make": vehicle.get("make") if vehicle else "",
                    "model": vehicle.get("model") if vehicle else "",
                    "vin": deal.vehicle_vin,
                    "price": f"${deal.vehicle_price:,.2f}"
                },
                "pricing": {
                    "vehicle_price": f"${deal.vehicle_price:,.2f}",
                    "dealer_discount": f"-${deal.dealer_discount:,.2f}" if deal.dealer_discount > 0 else "$0.00",
                    "rebates": f"-${deal.rebates:,.2f}" if deal.rebates > 0 else "$0.00",
                    "trade_allowance": f"-${deal.trade_in.net_trade_value:,.2f}" if deal.trade_in else "$0.00",
                    "fi_products": f"${sum(p.customer_price for p in deal.fi_products):,.2f}",
                    "taxes_fees": f"${self.calculate_tax_amount(deal.vehicle_price, deal.tax_info) + deal.tax_info.doc_fee:,.2f}"
                },
                "payment_info": {
                    "deal_type": deal.deal_type.title(),
                    "monthly_payment": f"${deal.monthly_payment:,.2f}",
                    "down_payment": f"${deal.finance_terms.down_payment if deal.finance_terms else deal.lease_terms.down_payment if deal.lease_terms else 0:,.2f}",
                    "term": f"{deal.finance_terms.term_months if deal.finance_terms else deal.lease_terms.term_months if deal.lease_terms else 0} months",
                    "apr": f"{deal.finance_terms.interest_rate if deal.finance_terms else 0:.2f}%"
                },
                "fi_products": [
                    {
                        "name": product.name,
                        "price": f"${product.customer_price:,.2f}",
                        "description": product.coverage_details
                    }
                    for product in deal.fi_products
                ],
                "total_cost": f"${deal.total_cost:,.2f}"
            }
            
            return proposal
            
        except Exception as e:
            logger.error(f"Error creating deal proposal: {str(e)}")
            return {}