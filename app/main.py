from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
import os

from app.config import get_settings
from app.routers import voice, appointment, crm

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Chicago Dental 312 AI Receptionist",
    description="AI-powered voice receptionist for dental clinic appointment scheduling",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(voice.router, prefix="/api/v1")
app.include_router(appointment.router, prefix="/api/v1")
app.include_router(crm.router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic info."""
    return f"""
    <html>
        <head>
            <title>Chicago Dental 312 AI Receptionist</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c5aa0;
                    border-bottom: 3px solid #2c5aa0;
                    padding-bottom: 10px;
                }}
                .status {{
                    display: inline-block;
                    background: #4CAF50;
                    color: white;
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-size: 14px;
                }}
                .links {{
                    margin-top: 20px;
                }}
                .links a {{
                    display: inline-block;
                    margin: 10px 10px 0 0;
                    padding: 10px 20px;
                    background: #2c5aa0;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                }}
                .links a:hover {{
                    background: #1e3d6f;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Chicago Dental 312 AI Receptionist</h1>
                <span class="status">Online</span>
                <p>AI-powered voice receptionist for appointment scheduling and patient support.</p>
                
                <div class="links">
                    <a href="/docs">API Documentation</a>
                    <a href="/redoc">ReDoc</a>
                    <a href="/api/v1/crm/faq">FAQ</a>
                </div>
                
                <h2>Features</h2>
                <ul>
                    <li>Voice call handling via Twilio</li>
                    <li>Appointment booking with calendar integration</li>
                    <li>CRM lead capture</li>
                    <li>SMS/Email notifications</li>
                    <li>FAQ support</li>
                    <li>Emergency prioritization</li>
                </ul>
                
                <h2>API Endpoints</h2>
                <ul>
                    <li><code>POST /api/v1/voice/incoming</code> - Handle incoming calls</li>
                    <li><code>POST /api/v1/voice/gather</code> - Process voice input</li>
                    <li><code>POST /api/v1/appointment/check-availability</code> - Check slots</li>
                    <li><code>POST /api/v1/appointment/book</code> - Book appointment</li>
                    <li><code>POST /api/v1/crm/save-lead</code> - Save lead</li>
                    <li><code>GET /api/v1/crm/faq</code> - Get FAQ</li>
                </ul>
            </div>
        </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Chicago Dental 312 AI Receptionist",
        "version": "1.0.0"
    }


@app.get("/dashboard")
async def dashboard():
    """Serve the dashboard HTML."""
    dashboard_path = os.path.join(static_dir, "dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    return {"error": "Dashboard not found"}


@app.get("/chat")
async def chat_page():
    """Serve the chat HTML interface."""
    chat_path = os.path.join(static_dir, "chat.html")
    if os.path.exists(chat_path):
        return FileResponse(chat_path)
    return {"error": "Chat page not found"}


@app.post("/api/v1/chat")
async def chat(message: dict = Body(...)):
    """Chat endpoint for text-based AI receptionist."""
    user_message = message.get("message", "").lower()
    
    if not user_message:
        return {"reply": "Hello! How can I help you with your dental care today?"}
    
    # Simple response logic for chat
    if "appointment" in user_message or "book" in user_message:
        return {"reply": "I'd be happy to help you book an appointment! Please call us at (312) 555-0123 or visit our office at 123 Dental Ave, Chicago, IL 60601."}
    elif "emergency" in user_message or "pain" in user_message:
        return {"reply": "If this is a dental emergency, please call us immediately at (312) 555-0123. We prioritize urgent cases and will see you as soon as possible."}
    elif "price" in user_message or "cost" in user_message or "insurance" in user_message:
        return {"reply": "We accept most major insurance plans. For specific pricing questions, please call (312) 555-0123 and our team will help you."}
    elif "hours" in user_message or "open" in user_message:
        return {"reply": "We're open Monday-Friday 9am-6pm, Saturday 10am-2pm. Closed Sundays."}
    elif "location" in user_message or "address" in user_message:
        return {"reply": "We're located at 123 Dental Ave, Chicago, IL 60601."}
    else:
        return {"reply": "I can help you with appointment booking, emergency care, pricing, or our hours. What would you like to know?"}


@app.get("/api/v1/agent/config")
async def get_agent_config():
    """Get agent configuration."""
    from app.agent.config import AGENT_CONFIG
    return AGENT_CONFIG


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
