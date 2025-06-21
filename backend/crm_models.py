# CRM Models - Comprehensive Communication System
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from enum import Enum

# Lead Management Models
class Lead(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Contact Information
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    
    # Lead Details
    source: str  # LeadSource
    status: str = "new"  # LeadStatus
    score: int = 0  # AI-calculated lead score (0-100)
    
    # Vehicle Interest
    interested_vehicles: List[str] = []  # Vehicle IDs or descriptions
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    trade_in_vehicle: Optional[str] = None
    financing_needed: bool = True
    
    # Sales Process
    assigned_salesperson: Optional[str] = None
    last_contacted: Optional[datetime] = None
    next_follow_up: Optional[datetime] = None
    appointment_date: Optional[datetime] = None
    
    # Communication Preferences
    preferred_contact_method: str = "email"  # CommunicationType
    contact_time_preference: Optional[str] = None  # "morning", "afternoon", "evening"
    
    # AI Insights
    ai_notes: Optional[str] = None
    communication_summary: Optional[str] = None
    buying_signals: List[str] = []
    
    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    converted_deal_id: Optional[str] = None

class Communication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Related Entities
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
    deal_id: Optional[str] = None
    
    # Communication Details
    type: str  # CommunicationType
    direction: str  # "inbound" or "outbound"
    subject: Optional[str] = None
    content: str
    
    # Recipients/Senders
    from_email: Optional[str] = None
    to_email: Optional[str] = None
    from_phone: Optional[str] = None
    to_phone: Optional[str] = None
    
    # Staff
    staff_member: Optional[str] = None
    
    # Status & Tracking
    status: str = "sent"  # CommunicationStatus
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    
    # AI Generated
    is_ai_generated: bool = False
    ai_prompt: Optional[str] = None
    ai_model: Optional[str] = None
    
    # Attachments
    attachments: List[str] = []
    
    # Analytics
    engagement_score: Optional[int] = None
    sentiment: Optional[str] = None  # "positive", "neutral", "negative"
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Task Details
    title: str
    description: Optional[str] = None
    type: str  # TaskType
    priority: str = "medium"  # "low", "medium", "high", "urgent"
    status: str = "pending"  # TaskStatus
    
    # Related Entities
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
    deal_id: Optional[str] = None
    
    # Assignment
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None
    
    # Scheduling
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # AI Automation
    is_ai_generated: bool = False
    auto_complete: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CommunicationTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Template Details
    name: str
    description: Optional[str] = None
    type: str  # CommunicationType
    category: str  # "welcome", "follow_up", "appointment", "promotional", etc.
    
    # Content
    subject: Optional[str] = None  # For emails
    content: str
    variables: List[str] = []  # List of variables like {first_name}, {vehicle}
    
    # AI Enhancement
    is_ai_enhanced: bool = False
    ai_personalization: bool = True
    
    # Usage
    usage_count: int = 0
    effectiveness_score: Optional[float] = None
    
    # Settings
    is_active: bool = True
    is_default: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CommunicationSequence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Sequence Details
    name: str
    description: Optional[str] = None
    trigger: str  # "new_lead", "appointment_set", "no_response", etc.
    
    # Steps
    steps: List[Dict[str, Any]] = []  # Each step has timing, template_id, conditions
    
    # Settings
    is_active: bool = True
    auto_start: bool = True
    
    # Analytics
    enrollment_count: int = 0
    completion_rate: Optional[float] = None
    conversion_rate: Optional[float] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AIAgent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Agent Details
    name: str
    type: str  # "lead_qualifier", "communicator", "scheduler", "follow_up"
    description: str
    
    # AI Configuration
    model: str = "gpt-4"
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 1000
    
    # Capabilities
    can_send_email: bool = True
    can_send_sms: bool = True
    can_schedule_appointments: bool = False
    can_update_leads: bool = True
    can_create_tasks: bool = True
    
    # Performance
    total_interactions: int = 0
    success_rate: Optional[float] = None
    avg_response_time: Optional[float] = None
    
    # Settings
    is_active: bool = True
    auto_respond: bool = True
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CampaignModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Campaign Details
    name: str
    description: Optional[str] = None
    type: str  # "email", "sms", "mixed"
    status: str = "draft"  # "draft", "active", "paused", "completed"
    
    # Targeting
    target_criteria: Dict[str, Any] = {}  # Lead filtering criteria
    excluded_leads: List[str] = []
    
    # Content
    template_id: Optional[str] = None
    subject: Optional[str] = None
    content: str
    
    # Scheduling
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    send_immediately: bool = False
    
    # Analytics
    total_recipients: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    opened_count: int = 0
    clicked_count: int = 0
    replied_count: int = 0
    unsubscribed_count: int = 0
    
    # AI Optimization
    ai_optimized: bool = False
    a_b_testing: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)