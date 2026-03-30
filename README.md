# Chicago Dental 312 AI Receptionist

An intelligent voice AI receptionist for dental clinic appointment scheduling and patient support.

## Features

- **Voice Call Handling**: Automated phone receptionist via Twilio
- **Appointment Booking**: Complete flow from inquiry to confirmation
- **Calendar Integration**: Google Calendar sync for availability
- **CRM Lead Capture**: Automatic patient data storage
- **SMS/Email Notifications**: Automated confirmations and reminders
- **FAQ Support**: Answers common patient questions
- **Emergency Prioritization**: Fast-track urgent cases

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
# API
SECRET_KEY=your-secret-key

# Twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=your-twilio-number

# Google Calendar
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_CALENDAR_ID=your-calendar-id

# SendGrid
SENDGRID_API_KEY=your-api-key

# Database
DATABASE_URL=sqlite:///./dental_receptionist.db
```

3. Run the server:
```bash
uvicorn app.main:app --reload
```

4. Access API docs at: `http://localhost:8000/docs`

## API Endpoints

- `POST /voice/incoming` - Handle incoming Twilio calls
- `POST /voice/gather` - Process voice input
- `POST /appointment/check-availability` - Check slot availability
- `POST /appointment/book` - Book appointment
- `POST /crm/save-lead` - Save lead to CRM
- `GET /faq` - Get FAQ responses

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration management
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py          # DB connection
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── conversation.py  # AI conversation handler
│   │   ├── intents.py       # Intent detection
│   │   └── config.py        # Agent configuration
│   ├── services/
│   │   ├── __init__.py
│   │   ├── calendar.py      # Google Calendar integration
│   │   ├── crm.py           # CRM lead management
│   │   ├── notifications.py  # SMS/Email service
│   │   └── voice.py         # Twilio voice handling
│   └── routers/
│       ├── __init__.py
│       ├── voice.py         # Voice call endpoints
│       ├── appointment.py   # Appointment endpoints
│       └── crm.py           # CRM endpoints
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## License

MIT
