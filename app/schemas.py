from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import date, time, datetime
from enum import Enum


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    SCHEDULED = "scheduled"
    CONVERTED = "converted"
    LOST = "lost"


class LeadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    reason: Optional[str] = None
    source: str = "phone_call"


class LeadResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str]
    reason: Optional[str]
    status: LeadStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


class AppointmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    appointment_date: date
    appointment_time: time
    reason: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str]
    appointment_date: date
    appointment_time: time
    reason: Optional[str]
    status: AppointmentStatus
    sms_sent: bool
    email_sent: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AvailabilityCheck(BaseModel):
    date: date
    time: Optional[time] = None
    preferred_time_range: Optional[str] = None  # e.g., "morning", "afternoon", "evening"


class AvailabilityResponse(BaseModel):
    is_available: bool
    requested_slot: Dict[str, Any]
    alternative_slots: List[Dict[str, Any]] = []
    message: str


class ConversationInput(BaseModel):
    call_sid: str
    phone_number: str
    speech_result: Optional[str] = None
    digits: Optional[str] = None


class ConversationResponse(BaseModel):
    response_text: str
    current_step: str
    is_complete: bool = False
    redirect_to_human: bool = False


class FAQQuery(BaseModel):
    question: str


class FAQResponse(BaseModel):
    question: str
    answer: str
    confidence: float


class VoiceWebhook(BaseModel):
    CallSid: str
    From: str
    To: str
    SpeechResult: Optional[str] = None
    Digits: Optional[str] = None
    CallStatus: Optional[str] = None


class NotificationRequest(BaseModel):
    appointment_id: int
    notification_type: str = "confirmation"  # confirmation, reminder, cancellation


class SMSSendRequest(BaseModel):
    to: str
    message: str


class EmailSendRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    html_body: Optional[str] = None
