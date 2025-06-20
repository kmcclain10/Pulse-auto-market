"""
Subscription Billing Service for Pulse Auto Market
Handles Stripe integration, subscriptions, and billing management
"""
import os
import uuid
import stripe
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum

from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    UNPAID = "unpaid"

class SubscriptionPlan(str, Enum):
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dealer_id: str
    dealer_name: str
    dealer_email: str
    stripe_customer_id: str
    stripe_subscription_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PaymentHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dealer_id: str
    stripe_invoice_id: str
    amount: float
    currency: str = "usd"
    status: str  # "paid", "failed", "pending"
    invoice_url: Optional[str] = None
    description: str = ""
    payment_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BillingUsage(BaseModel):
    dealer_id: str
    period_start: datetime
    period_end: datetime
    vehicles_listed: int = 0
    leads_processed: int = 0
    deals_calculated: int = 0
    api_calls: int = 0
    overage_charges: float = 0.0

class CreateSubscriptionRequest(BaseModel):
    dealer_id: str
    dealer_name: str
    dealer_email: str
    plan: SubscriptionPlan
    payment_method_id: str

class UpdateSubscriptionRequest(BaseModel):
    subscription_id: str
    new_plan: SubscriptionPlan

class BillingService:
    """Subscription billing and Stripe management service"""
    
    def __init__(self, db):
        self.db = db
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.trial_days = int(os.getenv('TRIAL_PERIOD_DAYS', 90))
        
        # Plan configurations with new pricing
        self.plans = {
            "basic": {
                "price_id": "price_basic_199",  # Replace with actual Stripe price ID
                "amount": 199.00,
                "name": "Basic Plan",
                "features": [
                    "Up to 100 vehicles",
                    "Basic inventory management", 
                    "Email support",
                    "Mobile-friendly interface",
                    "Basic reporting"
                ],
                "limits": {
                    "vehicles": 100,
                    "leads_per_month": 500,
                    "deals_per_month": 100,
                    "api_calls_per_month": 1000
                }
            },
            "professional": {
                "price_id": "price_professional_399",  # Replace with actual Stripe price ID
                "amount": 399.00,
                "name": "Professional Plan", 
                "features": [
                    "Up to 500 vehicles",
                    "Full AI CRM with lead scoring",
                    "Advanced desking tool",
                    "Image scraping (10+ photos per vehicle)",
                    "Deal Pulse price analysis",
                    "Priority support",
                    "Advanced reporting",
                    "F&I product management"
                ],
                "limits": {
                    "vehicles": 500,
                    "leads_per_month": 2000,
                    "deals_per_month": 500,
                    "api_calls_per_month": 5000
                }
            },
            "enterprise": {
                "price_id": "price_enterprise_999",  # Replace with actual Stripe price ID
                "amount": 999.00,
                "name": "Enterprise Plan",
                "features": [
                    "Unlimited vehicles",
                    "Full AI CRM with automation",
                    "Advanced desking tool with F&I optimization",
                    "Premium image scraping with CDN",
                    "Deal Pulse with market insights",
                    "Multi-location support",
                    "Custom integrations",
                    "24/7 dedicated support",
                    "White-label options",
                    "API access for partners",
                    "Advanced analytics dashboard"
                ],
                "limits": {
                    "vehicles": -1,  # Unlimited
                    "leads_per_month": -1,  # Unlimited
                    "deals_per_month": -1,  # Unlimited
                    "api_calls_per_month": -1  # Unlimited
                }
            }
        }
    
    async def create_subscription(self, request: CreateSubscriptionRequest) -> Dict:
        """Create a new subscription with 90-day free trial"""
        try:
            # Check if dealer already has a subscription
            existing = await self.db.subscriptions.find_one({"dealer_id": request.dealer_id})
            if existing:
                raise Exception("Dealer already has an active subscription")
            
            # Create or retrieve Stripe customer
            customers = stripe.Customer.list(email=request.dealer_email, limit=1)
            if customers.data:
                customer = customers.data[0]
            else:
                customer = stripe.Customer.create(
                    email=request.dealer_email,
                    name=request.dealer_name,
                    metadata={"dealer_id": request.dealer_id}
                )
            
            # Attach payment method to customer
            stripe.PaymentMethod.attach(
                request.payment_method_id,
                customer=customer.id
            )
            
            # Set as default payment method
            stripe.Customer.modify(
                customer.id,
                invoice_settings={'default_payment_method': request.payment_method_id}
            )
            
            # Create subscription with trial
            stripe_subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': self.plans[request.plan]["price_id"]}],
                trial_period_days=self.trial_days,
                metadata={
                    "dealer_id": request.dealer_id,
                    "dealer_name": request.dealer_name
                },
                expand=['latest_invoice.payment_intent']
            )
            
            # Create subscription record in database
            subscription = Subscription(
                dealer_id=request.dealer_id,
                dealer_name=request.dealer_name,
                dealer_email=request.dealer_email,
                stripe_customer_id=customer.id,
                stripe_subscription_id=stripe_subscription.id,
                plan=request.plan,
                status=stripe_subscription.status,
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                trial_end=datetime.fromtimestamp(stripe_subscription.trial_end) if stripe_subscription.trial_end else None
            )
            
            await self.db.subscriptions.insert_one(subscription.dict())
            
            # Initialize usage tracking
            usage = BillingUsage(
                dealer_id=request.dealer_id,
                period_start=subscription.current_period_start,
                period_end=subscription.current_period_end
            )
            await self.db.billing_usage.insert_one(usage.dict())
            
            logger.info(f"Created subscription for dealer {request.dealer_id}: {stripe_subscription.id}")
            
            return {
                "subscription_id": stripe_subscription.id,
                "status": stripe_subscription.status,
                "trial_end": stripe_subscription.trial_end,
                "plan": request.plan,
                "amount": self.plans[request.plan]["amount"],
                "message": f"Welcome to Pulse Auto Market! Your {self.trial_days}-day free trial has started."
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {str(e)}")
            raise Exception(f"Payment processing error: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            raise Exception(f"Failed to create subscription: {str(e)}")
    
    async def get_subscription_by_dealer(self, dealer_id: str) -> Optional[Subscription]:
        """Get subscription by dealer ID"""
        try:
            subscription_data = await self.db.subscriptions.find_one({"dealer_id": dealer_id})
            if subscription_data:
                return Subscription(**subscription_data)
            return None
        except Exception as e:
            logger.error(f"Error getting subscription for dealer {dealer_id}: {str(e)}")
            return None
    
    async def update_subscription_plan(self, request: UpdateSubscriptionRequest) -> Dict:
        """Update subscription plan with proration"""
        try:
            # Get current subscription from database
            subscription = await self.db.subscriptions.find_one(
                {"stripe_subscription_id": request.subscription_id}
            )
            if not subscription:
                raise Exception("Subscription not found")
            
            # Get current Stripe subscription
            stripe_subscription = stripe.Subscription.retrieve(request.subscription_id)
            
            # Update subscription in Stripe
            updated_subscription = stripe.Subscription.modify(
                request.subscription_id,
                items=[{
                    'id': stripe_subscription['items']['data'][0].id,
                    'price': self.plans[request.new_plan]["price_id"]
                }],
                proration_behavior='create_prorations'
            )
            
            # Update in database
            await self.db.subscriptions.update_one(
                {"stripe_subscription_id": request.subscription_id},
                {
                    "$set": {
                        "plan": request.new_plan,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Updated subscription {request.subscription_id} to {request.new_plan}")
            
            return {
                "message": "Subscription plan updated successfully",
                "new_plan": request.new_plan,
                "new_amount": self.plans[request.new_plan]["amount"]
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating subscription: {str(e)}")
            raise Exception(f"Payment processing error: {str(e)}")
        except Exception as e:
            logger.error(f"Error updating subscription: {str(e)}")
            raise Exception(f"Failed to update subscription: {str(e)}")
    
    async def cancel_subscription(self, subscription_id: str, immediate: bool = False) -> Dict:
        """Cancel subscription (immediate or at period end)"""
        try:
            if immediate:
                # Cancel immediately
                stripe.Subscription.delete(subscription_id)
                status = "canceled"
            else:
                # Cancel at period end
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
                status = "active"  # Still active until period end
            
            # Update in database
            await self.db.subscriptions.update_one(
                {"stripe_subscription_id": subscription_id},
                {
                    "$set": {
                        "status": status,
                        "cancel_at_period_end": not immediate,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            message = "Subscription canceled immediately" if immediate else "Subscription will cancel at end of billing period"
            logger.info(f"Canceled subscription {subscription_id}: {message}")
            
            return {"message": message}
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription: {str(e)}")
            raise Exception(f"Payment processing error: {str(e)}")
        except Exception as e:
            logger.error(f"Error canceling subscription: {str(e)}")
            raise Exception(f"Failed to cancel subscription: {str(e)}")
    
    async def get_payment_history(self, dealer_id: str, limit: int = 50) -> List[PaymentHistory]:
        """Get payment history for a dealer"""
        try:
            payments_data = await self.db.payment_history.find(
                {"dealer_id": dealer_id}
            ).sort("payment_date", -1).limit(limit).to_list(limit)
            
            return [PaymentHistory(**payment) for payment in payments_data]
        except Exception as e:
            logger.error(f"Error getting payment history for dealer {dealer_id}: {str(e)}")
            return []
    
    async def create_billing_portal_session(self, dealer_id: str) -> str:
        """Create Stripe billing portal session"""
        try:
            subscription = await self.db.subscriptions.find_one({"dealer_id": dealer_id})
            if not subscription:
                raise Exception("Subscription not found")
            
            session = stripe.billing_portal.Session.create(
                customer=subscription["stripe_customer_id"],
                return_url=os.getenv("FRONTEND_URL", "http://localhost:3000") + "/billing"
            )
            
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating billing portal: {str(e)}")
            raise Exception(f"Payment processing error: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating billing portal: {str(e)}")
            raise Exception(f"Failed to create billing portal: {str(e)}")
    
    async def track_usage(self, dealer_id: str, usage_type: str, count: int = 1):
        """Track usage for billing limits"""
        try:
            # Get current billing period
            subscription = await self.db.subscriptions.find_one({"dealer_id": dealer_id})
            if not subscription:
                return
            
            # Find current usage record
            usage = await self.db.billing_usage.find_one({
                "dealer_id": dealer_id,
                "period_start": {"$lte": datetime.utcnow()},
                "period_end": {"$gte": datetime.utcnow()}
            })
            
            if usage:
                # Update usage
                increment = {f"${usage_type}": count}
                await self.db.billing_usage.update_one(
                    {"_id": usage["_id"]},
                    {"$inc": increment}
                )
            
        except Exception as e:
            logger.error(f"Error tracking usage for dealer {dealer_id}: {str(e)}")
    
    async def check_usage_limits(self, dealer_id: str) -> Dict:
        """Check if dealer is within usage limits"""
        try:
            subscription = await self.db.subscriptions.find_one({"dealer_id": dealer_id})
            if not subscription:
                return {"within_limits": False, "message": "No active subscription"}
            
            plan_limits = self.plans[subscription["plan"]]["limits"]
            
            # Get current usage
            usage = await self.db.billing_usage.find_one({
                "dealer_id": dealer_id,
                "period_start": {"$lte": datetime.utcnow()},
                "period_end": {"$gte": datetime.utcnow()}
            })
            
            if not usage:
                return {"within_limits": True, "usage": {}, "limits": plan_limits}
            
            # Check each limit
            warnings = []
            blocked = []
            
            for limit_type, limit_value in plan_limits.items():
                if limit_value == -1:  # Unlimited
                    continue
                
                current_usage = usage.get(limit_type.replace("_per_month", ""), 0)
                usage_percentage = (current_usage / limit_value) * 100
                
                if current_usage >= limit_value:
                    blocked.append(f"{limit_type}: {current_usage}/{limit_value}")
                elif usage_percentage >= 80:
                    warnings.append(f"{limit_type}: {current_usage}/{limit_value} ({usage_percentage:.1f}%)")
            
            return {
                "within_limits": len(blocked) == 0,
                "warnings": warnings,
                "blocked": blocked,
                "usage": {
                    "vehicles": usage.get("vehicles_listed", 0),
                    "leads": usage.get("leads_processed", 0),
                    "deals": usage.get("deals_calculated", 0),
                    "api_calls": usage.get("api_calls", 0)
                },
                "limits": plan_limits
            }
            
        except Exception as e:
            logger.error(f"Error checking usage limits for dealer {dealer_id}: {str(e)}")
            return {"within_limits": False, "message": "Error checking limits"}
    
    async def get_billing_summary(self, dealer_id: str) -> Dict:
        """Get comprehensive billing summary for dealer"""
        try:
            subscription = await self.get_subscription_by_dealer(dealer_id)
            if not subscription:
                return {"error": "No subscription found"}
            
            # Get payment history
            payments = await self.get_payment_history(dealer_id, 12)  # Last 12 payments
            
            # Get usage limits
            usage_info = await self.check_usage_limits(dealer_id)
            
            # Calculate metrics
            total_paid = sum(p.amount for p in payments if p.status == "paid")
            failed_payments = len([p for p in payments if p.status == "failed"])
            
            # Days until next billing
            days_until_billing = (subscription.current_period_end - datetime.utcnow()).days
            
            return {
                "subscription": subscription.dict(),
                "plan_info": self.plans[subscription.plan],
                "usage": usage_info,
                "billing_metrics": {
                    "total_paid": total_paid,
                    "failed_payments": failed_payments,
                    "days_until_billing": days_until_billing,
                    "next_amount": self.plans[subscription.plan]["amount"]
                },
                "recent_payments": [p.dict() for p in payments[:5]]
            }
            
        except Exception as e:
            logger.error(f"Error getting billing summary for dealer {dealer_id}: {str(e)}")
            return {"error": str(e)}
    
    def get_plans(self) -> Dict:
        """Get all available plans"""
        return self.plans
    
    async def handle_webhook_event(self, event: Dict):
        """Handle Stripe webhook events"""
        try:
            event_type = event['type']
            data = event['data']['object']
            
            if event_type == 'customer.subscription.created':
                await self._handle_subscription_created(data)
            elif event_type == 'customer.subscription.updated':
                await self._handle_subscription_updated(data)
            elif event_type == 'customer.subscription.deleted':
                await self._handle_subscription_deleted(data)
            elif event_type == 'invoice.payment_succeeded':
                await self._handle_payment_succeeded(data)
            elif event_type == 'invoice.payment_failed':
                await self._handle_payment_failed(data)
            
            logger.info(f"Processed webhook event: {event_type}")
            
        except Exception as e:
            logger.error(f"Error handling webhook event {event.get('type')}: {str(e)}")
            raise
    
    async def _handle_subscription_created(self, subscription):
        """Handle subscription created webhook"""
        await self.db.subscriptions.update_one(
            {"stripe_subscription_id": subscription['id']},
            {
                "$set": {
                    "status": subscription['status'],
                    "current_period_start": datetime.fromtimestamp(subscription['current_period_start']),
                    "current_period_end": datetime.fromtimestamp(subscription['current_period_end']),
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    async def _handle_subscription_updated(self, subscription):
        """Handle subscription updated webhook"""
        await self.db.subscriptions.update_one(
            {"stripe_subscription_id": subscription['id']},
            {
                "$set": {
                    "status": subscription['status'],
                    "current_period_start": datetime.fromtimestamp(subscription['current_period_start']),
                    "current_period_end": datetime.fromtimestamp(subscription['current_period_end']),
                    "cancel_at_period_end": subscription.get('cancel_at_period_end', False),
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    async def _handle_subscription_deleted(self, subscription):
        """Handle subscription deleted webhook"""
        await self.db.subscriptions.update_one(
            {"stripe_subscription_id": subscription['id']},
            {
                "$set": {
                    "status": "canceled",
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    async def _handle_payment_succeeded(self, invoice):
        """Handle successful payment webhook"""
        # Find subscription by customer ID
        subscription = await self.db.subscriptions.find_one(
            {"stripe_customer_id": invoice['customer']}
        )
        
        if subscription:
            # Add payment to history
            payment = PaymentHistory(
                dealer_id=subscription["dealer_id"],
                stripe_invoice_id=invoice['id'],
                amount=invoice['amount_paid'] / 100,  # Convert from cents
                currency=invoice['currency'],
                status="paid",
                invoice_url=invoice.get('hosted_invoice_url'),
                description=f"Pulse Auto Market - {subscription['plan'].title()} Plan",
                payment_date=datetime.fromtimestamp(invoice['created'])
            )
            
            await self.db.payment_history.insert_one(payment.dict())
    
    async def _handle_payment_failed(self, invoice):
        """Handle failed payment webhook"""
        # Find subscription by customer ID
        subscription = await self.db.subscriptions.find_one(
            {"stripe_customer_id": invoice['customer']}
        )
        
        if subscription:
            # Add failed payment to history
            payment = PaymentHistory(
                dealer_id=subscription["dealer_id"],
                stripe_invoice_id=invoice['id'],
                amount=invoice['amount_due'] / 100,  # Convert from cents
                currency=invoice['currency'],
                status="failed",
                invoice_url=invoice.get('hosted_invoice_url'),
                description=f"Failed payment - Pulse Auto Market {subscription['plan'].title()} Plan",
                payment_date=datetime.fromtimestamp(invoice['created'])
            )
            
            await self.db.payment_history.insert_one(payment.dict())