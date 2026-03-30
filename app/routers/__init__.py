# API Routers module
from app.routers.voice import router as voice_router
from app.routers.appointment import router as appointment_router
from app.routers.crm import router as crm_router

__all__ = ['voice_router', 'appointment_router', 'crm_router']
