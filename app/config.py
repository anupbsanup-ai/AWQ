from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # API
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # Google Calendar
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_CALENDAR_ID: Optional[str] = None
    
    # SendGrid
    SENDGRID_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite:///./dental_receptionist.db"
    
    # Redis (for session storage)
    REDIS_URL: Optional[str] = None
    
    # Clinic
    CLINIC_NAME: str = "Chicago Dental 312"
    CLINIC_PHONE: str = "(312) 555-0123"
    CLINIC_EMAIL: str = "appointments@chicagodental312.com"
    CLINIC_ADDRESS: str = "123 Dental Ave, Chicago, IL 60601"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
