from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.database import get_db
from app.schemas import LeadCreate, AppointmentCreate, AvailabilityCheck
from app.services.crm import get_crm_service
from app.services.calendar import calendar_service
from app.services.notifications import notification_service
from app.services.voice import voice_service
from app.agent.conversation import ConversationManager
from app.agent.config import AGENT_CONFIG

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/incoming", response_class=PlainTextResponse)
async def handle_incoming_call(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...)
):
    """
    Handle incoming Twilio voice calls.
    Returns TwiML with greeting and gathers initial user input.
    """
    # Initialize conversation
    conversation = ConversationManager(CallSid, From)
    
    greeting = AGENT_CONFIG["greeting"]
    twiml = voice_service.create_twiml_response(
        message=greeting,
        gather_input=True,
        action_url="/voice/gather"
    )
    
    return Response(content=twiml, media_type="application/xml")


@router.post("/gather", response_class=PlainTextResponse)
async def handle_gathered_input(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    SpeechResult: Optional[str] = Form(None),
    Digits: Optional[str] = Form(None),
    CallStatus: Optional[str] = Form(None)
):
    """
    Handle gathered speech or DTMF input from Twilio.
    Processes user intent and returns appropriate response.
    """
    # Check if call is still active
    if CallStatus and CallStatus in ["completed", "busy", "failed", "no-answer", "canceled"]:
        # Close conversation session
        conversation = ConversationManager(CallSid, From)
        conversation.close_session()
        return Response(content="<Response><Hangup/></Response>", media_type="application/xml")
    
    # Initialize conversation manager
    conversation = ConversationManager(CallSid, From)
    
    # Process the input
    result = conversation.process_input(
        user_input=SpeechResult,
        digits=Digits
    )
    
    # Handle booking completion
    if result.get("booking_confirmed"):
        # Save lead and appointment
        data = conversation.get_collected_data()
        await _save_booking(From, data)
    
    # Handle emergency
    if result.get("is_emergency"):
        data = conversation.get_collected_data()
        await _save_emergency(From, data)
    
    # Generate TwiML response
    if result["is_complete"]:
        twiml = voice_service.create_hangup_response(result["response_text"])
    elif result["redirect_to_human"]:
        twiml = voice_service.create_transfer_response(
            result["response_text"],
            "+1-312-555-0100"  # Human receptionist number
        )
    else:
        twiml = voice_service.create_twiml_response(
            message=result["response_text"],
            gather_input=True,
            action_url="/voice/gather"
        )
    
    return Response(content=twiml, media_type="application/xml")


@router.post("/no-input", response_class=PlainTextResponse)
async def handle_no_input(
    CallSid: str = Form(...),
    From: str = Form(...)
):
    """Handle case when no input is received from user."""
    conversation = ConversationManager(CallSid, From)
    result = conversation.process_input(None)
    
    twiml = voice_service.create_twiml_response(
        message=result["response_text"],
        gather_input=True,
        action_url="/voice/gather"
    )
    
    return Response(content=twiml, media_type="application/xml")


@router.post("/status-callback")
async def handle_call_status(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    From: str = Form(...)
):
    """Handle call status callbacks from Twilio."""
    if CallStatus in ["completed", "failed", "busy", "no-answer"]:
        conversation = ConversationManager(CallSid, From)
        conversation.close_session()
    
    return {"status": "ok"}


async def _save_booking(phone: str, data: dict):
    """Save confirmed booking to CRM and calendar."""
    try:
        # Save lead
        lead_data = LeadCreate(
            name=data.get("name", "Unknown"),
            phone=phone,
            email=data.get("email"),
            reason=data.get("reason"),
            source="phone_call"
        )
        
        crm = get_crm_service()
        lead = crm.save_lead(lead_data)
        
        # Parse date and time
        from datetime import datetime, date, time as dt_time
        date_str = data.get("date", "")
        time_str = data.get("time", "")
        
        # Simple date parsing (enhance as needed)
        appt_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
        appt_time = datetime.strptime(time_str, "%H:%M").time() if time_str else dt_time(9, 0)
        
        # Create appointment
        appt_data = AppointmentCreate(
            name=data.get("name", "Unknown"),
            phone=phone,
            email=data.get("email"),
            appointment_date=appt_date,
            appointment_time=appt_time,
            reason=data.get("reason")
        )
        
        appointment = crm.convert_lead_to_appointment(lead.id, appt_data)
        
        # Book in calendar
        await calendar_service.book_appointment(
            name=data.get("name", "Unknown"),
            phone=phone,
            email=data.get("email"),
            appointment_date=appt_date,
            appointment_time=appt_time,
            reason=data.get("reason")
        )
        
        # Send notifications
        await notification_service.send_appointment_confirmation(
            phone=phone,
            email=data.get("email"),
            name=data.get("name", "Patient"),
            appointment_date=date_str,
            appointment_time=time_str
        )
        
    except Exception as e:
        print(f"Error saving booking: {e}")


async def _save_emergency(phone: str, data: dict):
    """Save emergency inquiry to CRM with high priority."""
    try:
        lead_data = LeadCreate(
            name="Emergency Caller",
            phone=phone,
            reason=data.get("reason", "Emergency - immediate attention needed"),
            source="emergency_call"
        )
        
        crm = get_crm_service()
        lead = crm.save_lead(lead_data)
        crm.update_lead_status(lead.id, "contacted", "URGENT: Emergency call - prioritize")
        
        # Send immediate notification to clinic staff
        await notification_service.send_sms(
            settings.CLINIC_PHONE,
            f"URGENT: Emergency call from {phone}. Reason: {data.get('reason', 'Unknown')}"
        )
        
    except Exception as e:
        print(f"Error saving emergency: {e}")


from app.config import get_settings
settings = get_settings()
