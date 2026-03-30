from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas import LeadCreate, LeadResponse, LeadStatus, FAQQuery, FAQResponse
from app.services.crm import get_crm_service
from app.agent.config import AGENT_CONFIG
from app.agent.intents import intent_detector

router = APIRouter(prefix="/crm", tags=["crm"])


@router.post("/save-lead", response_model=LeadResponse)
async def save_lead(
    lead: LeadCreate,
    db: Session = Depends(get_db)
):
    """
    Save or update a lead in the CRM.
    """
    crm = get_crm_service(db)
    saved_lead = crm.save_lead(lead)
    return saved_lead


@router.get("/leads", response_model=List[LeadResponse])
async def list_leads(
    status: Optional[LeadStatus] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all leads with optional status filter.
    """
    crm = get_crm_service(db)
    leads = crm.get_all_leads(
        status=status.value if status else None,
        limit=limit
    )
    return leads


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific lead by ID.
    """
    from app.models import Lead
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return lead


@router.get("/leads/by-phone/{phone}", response_model=LeadResponse)
async def get_lead_by_phone(
    phone: str,
    db: Session = Depends(get_db)
):
    """
    Get a lead by phone number.
    """
    crm = get_crm_service(db)
    lead = crm.get_lead_by_phone(phone)
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return lead


@router.patch("/leads/{lead_id}/status")
async def update_lead_status(
    lead_id: int,
    status: LeadStatus,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Update lead status.
    """
    crm = get_crm_service(db)
    success = crm.update_lead_status(lead_id, status.value, notes)
    
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {
        "success": True,
        "lead_id": lead_id,
        "new_status": status.value
    }


@router.get("/stats")
async def get_crm_stats(
    db: Session = Depends(get_db)
):
    """
    Get CRM statistics.
    """
    crm = get_crm_service(db)
    stats = crm.get_lead_stats()
    return stats


@router.get("/faq", response_model=List[dict])
async def get_all_faq():
    """
    Get all FAQ entries.
    """
    return AGENT_CONFIG["faq"]


@router.post("/faq/ask", response_model=FAQResponse)
async def ask_faq(query: FAQQuery):
    """
    Ask a question and get the best matching FAQ answer.
    """
    faq = intent_detector.match_faq(query.question)
    
    if faq:
        return FAQResponse(
            question=faq["question"],
            answer=faq["answer"],
            confidence=0.85
        )
    
    return FAQResponse(
        question=query.question,
        answer="I'm not sure about that. Let me connect you with our staff who can help better.",
        confidence=0.0
    )
