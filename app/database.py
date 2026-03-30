from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Date, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import get_settings

settings = get_settings()

# Support both SQLite (dev) and PostgreSQL (production)
database_url = settings.DATABASE_URL

if database_url and database_url.startswith("postgres"):
    # Production PostgreSQL on Fly.io
    engine = create_engine(database_url)
else:
    # Development SQLite
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Lead(Base):
    """CRM Lead model."""
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False, index=True)
    email = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    source = Column(String(50), default="phone_call")
    status = Column(String(20), default="new")  # new, contacted, scheduled, converted, lost
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)


class Appointment(Base):
    """Appointment model."""
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=True)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="scheduled")  # scheduled, confirmed, completed, cancelled, no_show
    google_calendar_event_id = Column(String(100), nullable=True)
    sms_sent = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationSession(Base):
    """Store conversation state for phone calls."""
    __tablename__ = "conversation_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    call_sid = Column(String(100), unique=True, index=True)
    phone_number = Column(String(20), nullable=False)
    current_step = Column(String(50), default="greeting")
    collected_data = Column(Text, default="{}")  # JSON string
    intent = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


# Create tables
Base.metadata.create_all(bind=engine)
