"""
AI-Powered CRM Service for Pulse Auto Market
Handles lead response automation, scoring, and conversation management
"""
import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum

from emergentintegrations.llm.chat import LlmChat, UserMessage
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    QUALIFIED = "qualified"
    CLOSED = "closed"
    LOST = "lost"

class LeadScore(str, Enum):
    HOT = "hot"          # Ready to buy, specific vehicle inquiry
    WARM = "warm"        # Interested, asking questions
    COLD = "cold"        # General browsing, price shopping

class InquiryType(str, Enum):
    PRICE = "price"
    AVAILABILITY = "availability"
    FINANCING = "financing"
    TRADE_IN = "trade_in"
    GENERAL = "general"
    APPOINTMENT = "appointment"

class Lead(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_name: str = ""
    customer_email: str
    customer_phone: str = ""
    vehicle_vin: Optional[str] = None
    inquiry_type: InquiryType = InquiryType.GENERAL
    message: str
    dealer_id: str
    dealer_name: str
    lead_score: LeadScore = LeadScore.COLD
    status: LeadStatus = LeadStatus.NEW
    ai_response: Optional[str] = None
    ai_response_approved: bool = False
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_contact: Optional[datetime] = None
    follow_up_count: int = 0

class ConversationMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    sender: str  # "customer", "ai", "dealer"
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    vehicle_vin: Optional[str] = None

class AIResponse(BaseModel):
    response_text: str
    confidence: float
    suggested_next_actions: List[str]
    inquiry_type: InquiryType
    lead_score: LeadScore

class AutomationSettings(BaseModel):
    dealer_id: str
    ai_enabled: bool = True
    auto_respond: bool = False  # If True, sends AI response without approval
    response_delay_minutes: int = 5
    business_hours_only: bool = True
    business_hours_start: str = "08:00"
    business_hours_end: str = "18:00"
    max_follow_ups: int = 3
    follow_up_intervals: List[int] = [24, 72, 168]  # Hours between follow-ups

class AICRMService:
    """AI-powered CRM service for automotive dealerships"""
    
    def __init__(self, db):
        self.db = db
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.system_message = self._create_system_message()
    
    def _create_system_message(self) -> str:
        """Create the AI system message for automotive sales"""
        return """You are an expert automotive sales assistant for a car dealership. Your role is to:

1. Respond professionally and enthusiastically to customer vehicle inquiries
2. Provide helpful information about vehicles, pricing, and dealership services
3. Create urgency and excitement about the vehicles
4. Guide customers toward scheduling a visit or phone call
5. Be knowledgeable about automotive financing, trade-ins, and features

Guidelines:
- Always be professional, friendly, and helpful
- Include specific vehicle details when available
- Mention financing options and trade-in possibilities
- Create urgency (limited inventory, special offers)
- Always include dealer contact information
- Ask qualifying questions to understand customer needs
- Use automotive sales terminology appropriately
- Keep responses concise but informative (2-3 paragraphs max)

Never:
- Quote exact prices (say "competitive pricing" or "great value")
- Make commitments about financing approval
- Give false information about vehicle availability
- Be pushy or aggressive
"""
    
    async def classify_inquiry_type(self, message: str) -> InquiryType:
        """Classify the type of customer inquiry"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['price', 'cost', 'payment', 'monthly', '$']):
            return InquiryType.PRICE
        elif any(word in message_lower for word in ['available', 'stock', 'inventory', 'still have']):
            return InquiryType.AVAILABILITY
        elif any(word in message_lower for word in ['finance', 'loan', 'credit', 'approve', 'down payment']):
            return InquiryType.FINANCING
        elif any(word in message_lower for word in ['trade', 'trade-in', 'my car', 'current vehicle']):
            return InquiryType.TRADE_IN
        elif any(word in message_lower for word in ['appointment', 'visit', 'see', 'test drive', 'come in']):
            return InquiryType.APPOINTMENT
        else:
            return InquiryType.GENERAL
    
    async def calculate_lead_score(self, message: str, inquiry_type: InquiryType, customer_info: Dict) -> LeadScore:
        """Calculate lead score based on message content and customer info"""
        score_points = 0
        message_lower = message.lower()
        
        # Hot signals
        hot_signals = [
            'ready to buy', 'cash buyer', 'this weekend', 'today', 'tomorrow',
            'test drive', 'appointment', 'come in', 'financing approved'
        ]
        
        # Warm signals  
        warm_signals = [
            'interested', 'considering', 'looking at', 'thinking about',
            'financing', 'trade-in', 'monthly payment'
        ]
        
        # Cold signals
        cold_signals = [
            'just looking', 'browsing', 'maybe', 'might', 'eventually',
            'just curious', 'research'
        ]
        
        if any(signal in message_lower for signal in hot_signals):
            score_points += 3
        elif any(signal in message_lower for signal in warm_signals):
            score_points += 2
        elif any(signal in message_lower for signal in cold_signals):
            score_points -= 1
        
        # Inquiry type scoring
        if inquiry_type in [InquiryType.APPOINTMENT, InquiryType.FINANCING]:
            score_points += 2
        elif inquiry_type in [InquiryType.PRICE, InquiryType.TRADE_IN]:
            score_points += 1
        
        # Customer info scoring
        if customer_info.get('phone'):
            score_points += 1
        
        # Message length (longer messages often indicate higher interest)
        if len(message) > 100:
            score_points += 1
        
        # Determine final score
        if score_points >= 4:
            return LeadScore.HOT
        elif score_points >= 2:
            return LeadScore.WARM
        else:
            return LeadScore.COLD
    
    async def generate_ai_response(self, lead: Lead, vehicle_info: Optional[Dict] = None) -> AIResponse:
        """Generate AI response for a customer inquiry"""
        try:
            # Create chat session
            chat = LlmChat(
                api_key=self.openai_key,
                session_id=lead.conversation_id,
                system_message=self.system_message
            ).with_model("openai", "gpt-4o")
            
            # Prepare context information
            context_parts = [
                f"Customer inquiry: {lead.message}",
                f"Customer name: {lead.customer_name or 'Customer'}",
                f"Inquiry type: {lead.inquiry_type}",
                f"Dealer: {lead.dealer_name}"
            ]
            
            if vehicle_info:
                vehicle_context = f"""
Vehicle Information:
- {vehicle_info.get('year', '')} {vehicle_info.get('make', '')} {vehicle_info.get('model', '')}
- VIN: {vehicle_info.get('vin', '')}
- Mileage: {vehicle_info.get('mileage', 0):,} miles
- Price: ${vehicle_info.get('price', 0):,}
- Location: {vehicle_info.get('dealer_location', '')}
- Features: {vehicle_info.get('fuel_type', '')}, {vehicle_info.get('transmission', '')}, {vehicle_info.get('drivetrain', '')}
"""
                context_parts.append(vehicle_context)
            
            # Create prompt
            prompt = "\n\n".join(context_parts) + "\n\nPlease write a professional response to this customer inquiry."
            
            # Send message to AI
            user_message = UserMessage(text=prompt)
            ai_response = await chat.send_message(user_message)
            
            # Classify inquiry type from response
            inquiry_type = await self.classify_inquiry_type(lead.message)
            
            # Calculate lead score
            customer_info = {
                'phone': lead.customer_phone,
                'email': lead.customer_email
            }
            lead_score = await self.calculate_lead_score(lead.message, inquiry_type, customer_info)
            
            # Suggest next actions based on score and inquiry type
            next_actions = self._suggest_next_actions(lead_score, inquiry_type)
            
            return AIResponse(
                response_text=ai_response,
                confidence=0.85,  # Could be enhanced with actual confidence scoring
                suggested_next_actions=next_actions,
                inquiry_type=inquiry_type,
                lead_score=lead_score
            )
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            # Fallback response
            return AIResponse(
                response_text=self._get_fallback_response(lead.inquiry_type),
                confidence=0.5,
                suggested_next_actions=["Schedule follow-up call"],
                inquiry_type=lead.inquiry_type,
                lead_score=LeadScore.COLD
            )
    
    def _suggest_next_actions(self, lead_score: LeadScore, inquiry_type: InquiryType) -> List[str]:
        """Suggest next actions based on lead score and inquiry type"""
        actions = []
        
        if lead_score == LeadScore.HOT:
            actions.extend([
                "Call immediately",
                "Schedule test drive",
                "Prepare financing options"
            ])
        elif lead_score == LeadScore.WARM:
            actions.extend([
                "Send follow-up email",
                "Schedule phone call",
                "Send additional vehicle photos"
            ])
        else:  # COLD
            actions.extend([
                "Add to nurture campaign",
                "Send market report",
                "Follow up in 1 week"
            ])
        
        # Add inquiry-specific actions
        if inquiry_type == InquiryType.FINANCING:
            actions.append("Prepare financing pre-approval")
        elif inquiry_type == InquiryType.TRADE_IN:
            actions.append("Schedule trade-in appraisal")
        elif inquiry_type == InquiryType.APPOINTMENT:
            actions.append("Confirm appointment details")
        
        return actions
    
    def _get_fallback_response(self, inquiry_type: InquiryType) -> str:
        """Get fallback response when AI fails"""
        fallback_responses = {
            InquiryType.PRICE: "Thank you for your interest! We offer competitive pricing and flexible financing options. I'd love to discuss the details with you personally. Please call us or visit our showroom for a personalized quote.",
            InquiryType.AVAILABILITY: "Thank you for inquiring about this vehicle! We update our inventory daily and would be happy to check current availability for you. Please contact us directly for the most up-to-date information.",
            InquiryType.FINANCING: "We work with multiple lenders to help you get the best financing terms possible. Our finance team can help you explore your options and get pre-approved. Please give us a call to discuss your financing needs.",
            InquiryType.TRADE_IN: "We accept trade-ins and can provide you with a competitive appraisal. Bring your current vehicle by our showroom for a free evaluation, or provide us with details for a preliminary estimate.",
            InquiryType.APPOINTMENT: "We'd be delighted to schedule a time for you to see this vehicle! Our showroom is open daily and we can arrange for a test drive. Please call us or reply with your preferred times.",
            InquiryType.GENERAL: "Thank you for your interest! We're here to help you find the perfect vehicle. Please don't hesitate to contact us with any questions or to schedule a visit to our showroom."
        }
        
        return fallback_responses.get(inquiry_type, fallback_responses[InquiryType.GENERAL])
    
    async def process_new_lead(self, lead_data: Dict) -> Lead:
        """Process a new lead and generate AI response"""
        try:
            # Create lead object
            lead = Lead(**lead_data)
            
            # Get vehicle information if VIN provided
            vehicle_info = None
            if lead.vehicle_vin:
                vehicle = await self.db.vehicles.find_one({"vin": lead.vehicle_vin})
                if vehicle:
                    vehicle_info = vehicle
            
            # Generate AI response
            ai_response = await self.generate_ai_response(lead, vehicle_info)
            
            # Update lead with AI insights
            lead.ai_response = ai_response.response_text
            lead.inquiry_type = ai_response.inquiry_type
            lead.lead_score = ai_response.lead_score
            
            # Store lead in database
            await self.db.leads.insert_one(lead.dict())
            
            # Store initial conversation message
            customer_message = ConversationMessage(
                conversation_id=lead.conversation_id,
                sender="customer",
                message=lead.message,
                vehicle_vin=lead.vehicle_vin
            )
            await self.db.conversations.insert_one(customer_message.dict())
            
            # Store AI response message
            ai_message = ConversationMessage(
                conversation_id=lead.conversation_id,
                sender="ai",
                message=ai_response.response_text,
                vehicle_vin=lead.vehicle_vin
            )
            await self.db.conversations.insert_one(ai_message.dict())
            
            logger.info(f"Processed new lead: {lead.id}, Score: {lead.lead_score}")
            
            return lead
            
        except Exception as e:
            logger.error(f"Error processing new lead: {str(e)}")
            raise
    
    async def get_leads_for_dealer(self, dealer_id: str, status: Optional[LeadStatus] = None, 
                                 limit: int = 50) -> List[Lead]:
        """Get leads for a specific dealer"""
        try:
            query = {"dealer_id": dealer_id}
            if status:
                query["status"] = status
            
            leads_data = await self.db.leads.find(query).sort("created_at", -1).limit(limit).to_list(limit)
            return [Lead(**lead) for lead in leads_data]
            
        except Exception as e:
            logger.error(f"Error getting leads for dealer {dealer_id}: {str(e)}")
            return []
    
    async def update_lead_status(self, lead_id: str, status: LeadStatus, notes: str = "") -> bool:
        """Update lead status"""
        try:
            update_data = {
                "status": status,
                "last_contact": datetime.utcnow()
            }
            
            result = await self.db.leads.update_one(
                {"id": lead_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating lead status: {str(e)}")
            return False
    
    async def approve_ai_response(self, lead_id: str, approved: bool = True, 
                                custom_response: Optional[str] = None) -> bool:
        """Approve or modify AI response"""
        try:
            update_data = {"ai_response_approved": approved}
            
            if custom_response:
                update_data["ai_response"] = custom_response
            
            result = await self.db.leads.update_one(
                {"id": lead_id},
                {"$set": update_data}
            )
            
            # If approved, add dealer response to conversation
            if approved:
                lead = await self.db.leads.find_one({"id": lead_id})
                if lead:
                    dealer_message = ConversationMessage(
                        conversation_id=lead["conversation_id"],
                        sender="dealer",
                        message=custom_response or lead["ai_response"],
                        vehicle_vin=lead.get("vehicle_vin")
                    )
                    await self.db.conversations.insert_one(dealer_message.dict())
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error approving AI response: {str(e)}")
            return False
    
    async def get_conversation_history(self, conversation_id: str) -> List[ConversationMessage]:
        """Get conversation history"""
        try:
            messages_data = await self.db.conversations.find(
                {"conversation_id": conversation_id}
            ).sort("timestamp", 1).to_list(100)
            
            return [ConversationMessage(**msg) for msg in messages_data]
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
    
    async def generate_follow_up_sequences(self, dealer_id: str) -> List[Dict]:
        """Generate follow-up sequences for leads that need attention"""
        try:
            # Find leads that need follow-up
            follow_up_time = datetime.utcnow() - timedelta(hours=24)
            
            leads_needing_followup = await self.db.leads.find({
                "dealer_id": dealer_id,
                "status": {"$in": [LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.INTERESTED]},
                "last_contact": {"$lt": follow_up_time},
                "follow_up_count": {"$lt": 3}
            }).to_list(50)
            
            follow_up_suggestions = []
            
            for lead_data in leads_needing_followup:
                lead = Lead(**lead_data)
                
                # Generate follow-up message based on lead score and time since last contact
                follow_up_type = self._determine_follow_up_type(lead)
                follow_up_message = await self._generate_follow_up_message(lead, follow_up_type)
                
                follow_up_suggestions.append({
                    "lead_id": lead.id,
                    "customer_name": lead.customer_name,
                    "follow_up_type": follow_up_type,
                    "suggested_message": follow_up_message,
                    "priority": lead.lead_score,
                    "days_since_contact": (datetime.utcnow() - (lead.last_contact or lead.created_at)).days
                })
            
            return follow_up_suggestions
            
        except Exception as e:
            logger.error(f"Error generating follow-up sequences: {str(e)}")
            return []
    
    def _determine_follow_up_type(self, lead: Lead) -> str:
        """Determine appropriate follow-up type based on lead characteristics"""
        days_since_contact = (datetime.utcnow() - (lead.last_contact or lead.created_at)).days
        
        if lead.lead_score == LeadScore.HOT:
            return "urgent_call" if days_since_contact >= 1 else "same_day_follow_up"
        elif lead.lead_score == LeadScore.WARM:
            return "personal_email" if days_since_contact >= 2 else "check_in_call"
        else:
            return "nurture_email" if days_since_contact >= 7 else "market_update"
    
    async def _generate_follow_up_message(self, lead: Lead, follow_up_type: str) -> str:
        """Generate personalized follow-up message"""
        templates = {
            "urgent_call": f"Hi {lead.customer_name}, I wanted to follow up on your interest in the vehicle. Are you still looking? I have some great financing options available.",
            "personal_email": f"Hello {lead.customer_name}, I hope you're doing well. I wanted to reach out about the vehicle you inquired about. We have some new inventory that might interest you.",
            "nurture_email": f"Hi {lead.customer_name}, I wanted to check in and see how your vehicle search is going. We have some exciting new arrivals that might be perfect for you.",
            "market_update": f"Hello {lead.customer_name}, I thought you'd be interested in our latest market report and new vehicle arrivals."
        }
        
        return templates.get(follow_up_type, templates["nurture_email"])
    
    async def get_dealer_crm_stats(self, dealer_id: str) -> Dict:
        """Get CRM statistics for a dealer"""
        try:
            # Count leads by status
            pipeline = [
                {"$match": {"dealer_id": dealer_id}},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            status_counts = await self.db.leads.aggregate(pipeline).to_list(10)
            
            # Count leads by score
            score_pipeline = [
                {"$match": {"dealer_id": dealer_id}},
                {"$group": {"_id": "$lead_score", "count": {"$sum": 1}}}
            ]
            score_counts = await self.db.leads.aggregate(score_pipeline).to_list(10)
            
            # Get conversion rate
            total_leads = await self.db.leads.count_documents({"dealer_id": dealer_id})
            closed_leads = await self.db.leads.count_documents({
                "dealer_id": dealer_id,
                "status": LeadStatus.CLOSED
            })
            
            conversion_rate = (closed_leads / total_leads * 100) if total_leads > 0 else 0
            
            # Get recent activity
            recent_leads = await self.db.leads.count_documents({
                "dealer_id": dealer_id,
                "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}
            })
            
            return {
                "total_leads": total_leads,
                "recent_leads": recent_leads,
                "conversion_rate": round(conversion_rate, 1),
                "status_breakdown": {item["_id"]: item["count"] for item in status_counts},
                "score_breakdown": {item["_id"]: item["count"] for item in score_counts},
                "ai_responses_generated": await self.db.leads.count_documents({
                    "dealer_id": dealer_id,
                    "ai_response": {"$ne": None}
                }),
                "pending_approval": await self.db.leads.count_documents({
                    "dealer_id": dealer_id,
                    "ai_response": {"$ne": None},
                    "ai_response_approved": False
                })
            }
            
        except Exception as e:
            logger.error(f"Error getting CRM stats for dealer {dealer_id}: {str(e)}")
            return {}