from typing import Optional, Dict
from app.database import get_db
from app.models import Lead, Appointment
from app.schemas import LeadCreate, AppointmentCreate
from sqlalchemy.orm import Session


class CRMService:
    """CRM integration for lead capture and patient management."""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
    
    def save_lead(self, lead_data: LeadCreate) -> Lead:
        """
        Save a new lead to the CRM.
        Creates new or updates existing lead by phone number.
        """
        # Check if lead exists
        existing_lead = self.db.query(Lead).filter(
            Lead.phone == lead_data.phone
        ).first()
        
        if existing_lead:
            # Update existing lead
            existing_lead.name = lead_data.name
            if lead_data.email:
                existing_lead.email = lead_data.email
            if lead_data.reason:
                existing_lead.reason = lead_data.reason
            existing_lead.status = "contacted"
            existing_lead.source = lead_data.source
            self.db.commit()
            self.db.refresh(existing_lead)
            return existing_lead
        
        # Create new lead
        new_lead = Lead(
            name=lead_data.name,
            phone=lead_data.phone,
            email=lead_data.email,
            reason=lead_data.reason,
            source=lead_data.source,
            status="new"
        )
        self.db.add(new_lead)
        self.db.commit()
        self.db.refresh(new_lead)
        return new_lead
    
    def get_lead_by_phone(self, phone: str) -> Optional[Lead]:
        """Retrieve lead by phone number."""
        return self.db.query(Lead).filter(Lead.phone == phone).first()
    
    def update_lead_status(self, lead_id: int, status: str, notes: Optional[str] = None) -> bool:
        """Update lead status."""
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return False
        
        lead.status = status
        if notes:
            lead.notes = notes
        self.db.commit()
        return True
    
    def get_all_leads(self, status: Optional[str] = None, limit: int = 100) -> list:
        """Get all leads, optionally filtered by status."""
        query = self.db.query(Lead)
        if status:
            query = query.filter(Lead.status == status)
        return query.order_by(Lead.created_at.desc()).limit(limit).all()
    
    def convert_lead_to_appointment(
        self, 
        lead_id: int, 
        appointment_data: AppointmentCreate
    ) -> Appointment:
        """Convert a lead to a scheduled appointment."""
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.status = "converted"
            self.db.commit()
        
        appointment = Appointment(
            lead_id=lead_id,
            name=appointment_data.name,
            phone=appointment_data.phone,
            email=appointment_data.email,
            appointment_date=appointment_data.appointment_date,
            appointment_time=appointment_data.appointment_time,
            reason=appointment_data.reason,
            status="scheduled"
        )
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        return appointment
    
    def get_lead_stats(self) -> Dict:
        """Get CRM statistics."""
        total = self.db.query(Lead).count()
        by_status = {}
        for status in ["new", "contacted", "scheduled", "converted", "lost"]:
            count = self.db.query(Lead).filter(Lead.status == status).count()
            by_status[status] = count
        
        today_new = self.db.query(Lead).filter(
            Lead.created_at >= "today"
        ).count()
        
        return {
            "total_leads": total,
            "by_status": by_status,
            "today_new": today_new
        }


def get_crm_service(db: Session = None) -> CRMService:
    """Factory function to get CRM service instance."""
    return CRMService(db)
