# Services module
from app.services.calendar import CalendarService, calendar_service
from app.services.crm import CRMService, get_crm_service
from app.services.notifications import NotificationService, notification_service
from app.services.voice import VoiceService, voice_service

__all__ = [
    'CalendarService', 'calendar_service',
    'CRMService', 'get_crm_service',
    'NotificationService', 'notification_service',
    'VoiceService', 'voice_service'
]
