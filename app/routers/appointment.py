from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, time

from app.database import get_db
from app.schemas import (
    AppointmentCreate, 
    AppointmentResponse, 
    AvailabilityCheck,
    AvailabilityResponse,
    AppointmentStatus
)
from app.services.calendar import calendar_service
from app.services.crm import get_crm_service

router = APIRouter(prefix="/appointment", tags=["appointments"])


@router.post("/check-availability", response_model=AvailabilityResponse)
async def check_availability(
    availability_check: AvailabilityCheck,
    db: Session = Depends(get_db)
):
    """
    Check if a time slot is available and get alternative suggestions.
    """
    result = await calendar_service.check_availability(
        check_date=availability_check.date,
        check_time=availability_check.time,
        preferred_range=availability_check.preferred_time_range
    )
    
    return AvailabilityResponse(**result)


@router.post("/book", response_model=dict)
async def book_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db)
):
    """
    Book a new appointment.
    Saves to database, calendar, and CRM.
    """
    # Check availability first
    availability = await calendar_service.check_availability(
        check_date=appointment.appointment_date,
        check_time=appointment.appointment_time
    )
    
    if not availability["is_available"]:
        raise HTTPException(
            status_code=400,
            detail="The requested time slot is no longer available."
        )
    
    # Save lead to CRM
    from app.schemas import LeadCreate
    lead_data = LeadCreate(
        name=appointment.name,
        phone=appointment.phone,
        email=appointment.email,
        reason=appointment.reason,
        source="api_booking"
    )
    
    crm = get_crm_service(db)
    lead = crm.save_lead(lead_data)
    
    # Create appointment
    appt = crm.convert_lead_to_appointment(lead.id, appointment)
    
    # Book in Google Calendar
    calendar_result = await calendar_service.book_appointment(
        name=appointment.name,
        phone=appointment.phone,
        email=appointment.email,
        appointment_date=appointment.appointment_date,
        appointment_time=appointment.appointment_time,
        reason=appointment.reason
    )
    
    # Send notifications
    from app.services.notifications import notification_service
    await notification_service.send_appointment_confirmation(
        phone=appointment.phone,
        email=appointment.email,
        name=appointment.name,
        appointment_date=appointment.appointment_date.isoformat(),
        appointment_time=appointment.appointment_time.strftime("%I:%M %p")
    )
    
    return {
        "success": True,
        "appointment_id": appt.id,
        "lead_id": lead.id,
        "calendar_event_id": calendar_result.get("event_id"),
        "message": "Appointment booked successfully."
    }


@router.get("/list", response_model=List[AppointmentResponse])
async def list_appointments(
    date: Optional[date] = None,
    status: Optional[AppointmentStatus] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List appointments with optional filters.
    """
    from app.models import Appointment
    
    query = db.query(Appointment)
    
    if date:
        query = query.filter(Appointment.appointment_date == date)
    
    if status:
        query = query.filter(Appointment.status == status.value)
    
    appointments = query.order_by(Appointment.appointment_date, Appointment.appointment_time).limit(limit).all()
    
    return appointments


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific appointment by ID.
    """
    from app.models import Appointment
    
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return appointment


@router.patch("/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: int,
    status: AppointmentStatus,
    db: Session = Depends(get_db)
):
    """
    Update appointment status (e.g., confirmed, cancelled, completed).
    """
    from app.models import Appointment
    
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    appointment.status = status.value
    db.commit()
    db.refresh(appointment)
    
    return {
        "success": True,
        "appointment_id": appointment_id,
        "new_status": status.value
    }


@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel an appointment.
    """
    from app.models import Appointment
    
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Cancel in calendar
    if appointment.google_calendar_event_id:
        await calendar_service.cancel_appointment(appointment.google_calendar_event_id)
    
    # Update status
    appointment.status = "cancelled"
    db.commit()
    
    return {
        "success": True,
        "message": "Appointment cancelled successfully."
    }
