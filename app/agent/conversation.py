import json
import re
from datetime import datetime, date, time, timedelta
from typing import Dict, Optional, Any, Tuple
from app.agent.config import AGENT_CONFIG
from app.agent.intents import intent_detector
from app.database import get_db
from app.models import ConversationSession


class ConversationManager:
    """Manage AI receptionist conversation flow."""
    
    def __init__(self, call_sid: str, phone_number: str):
        self.call_sid = call_sid
        self.phone_number = phone_number
        self.session = self._get_or_create_session()
        self.collected_data = self._load_collected_data()
        
    def _get_or_create_session(self) -> ConversationSession:
        """Get existing session or create new one."""
        db = next(get_db())
        session = db.query(ConversationSession).filter(
            ConversationSession.call_sid == self.call_sid
        ).first()
        
        if not session:
            session = ConversationSession(
                call_sid=self.call_sid,
                phone_number=self.phone_number,
                current_step="greeting",
                collected_data="{}"
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        
        return session
    
    def _load_collected_data(self) -> Dict[str, Any]:
        """Load collected data from session."""
        try:
            return json.loads(self.session.collected_data) if self.session.collected_data else {}
        except:
            return {}
    
    def _save_session(self):
        """Save session state to database."""
        db = next(get_db())
        self.session.collected_data = json.dumps(self.collected_data)
        db.commit()
    
    def process_input(self, user_input: Optional[str], digits: Optional[str] = None) -> Dict[str, Any]:
        """
        Process user input and determine next response.
        Returns dict with response_text, current_step, is_complete, redirect_to_human
        """
        # Handle DTMF (button press) input
        if digits:
            return self._handle_digit_input(digits)
        
        if not user_input:
            return self._no_input_response()
        
        user_input = user_input.strip()
        
        # Check for goodbye
        if intent_detector.is_goodbye(user_input):
            return {
                "response_text": AGENT_CONFIG["closing"],
                "current_step": "closing",
                "is_complete": True,
                "redirect_to_human": False
            }
        
        # Route based on current step
        current_step = self.session.current_step
        intent = self.session.intent
        
        if current_step == "greeting":
            return self._handle_greeting(user_input)
        
        if intent == "emergency":
            return self._handle_emergency_flow(user_input, current_step)
        
        if intent == "faq":
            return self._handle_faq_flow(user_input, current_step)
        
        if intent == "book_appointment":
            return self._handle_booking_flow(user_input, current_step)
        
        # Unknown intent, try to detect again
        detected_intent, confidence = intent_detector.detect_intent(user_input)
        if confidence > 0.7:
            self.session.intent = detected_intent
            self._save_session()
            return self.process_input(user_input)
        
        # Still unknown, fallback
        return {
            "response_text": AGENT_CONFIG["fallback"]["unknown"],
            "current_step": current_step,
            "is_complete": False,
            "redirect_to_human": False
        }
    
    def _handle_greeting(self, user_input: str) -> Dict[str, Any]:
        """Handle initial greeting and intent detection."""
        intent, confidence = intent_detector.detect_intent(user_input)
        
        if intent == "emergency":
            self.session.intent = "emergency"
            self.session.current_step = "emergency_assess"
            self._save_session()
            return {
                "response_text": "I understand this is an emergency. Can you briefly tell me what's happening so I can get you the fastest help?",
                "current_step": "emergency_assess",
                "is_complete": False,
                "redirect_to_human": False
            }
        
        elif intent == "book_appointment":
            self.session.intent = "book_appointment"
            self.session.current_step = "collect_name"
            self._save_session()
            return {
                "response_text": "I'd be happy to help you schedule an appointment. " + AGENT_CONFIG["data_collection"]["collect_name"]["prompt"],
                "current_step": "collect_name",
                "is_complete": False,
                "redirect_to_human": False
            }
        
        elif intent == "faq":
            self.session.intent = "faq"
            faq = intent_detector.match_faq(user_input)
            if faq:
                return {
                    "response_text": faq["answer"] + " Is there anything else I can help you with?",
                    "current_step": "faq_followup",
                    "is_complete": False,
                    "redirect_to_human": False
                }
            else:
                return {
                    "response_text": "I'd be happy to answer your questions. What would you like to know about our services?",
                    "current_step": "faq_general",
                    "is_complete": False,
                    "redirect_to_human": False
                }
        
        else:
            # Unclear intent, ask for clarification
            return {
                "response_text": "I can help you book an appointment or answer questions about our services. What would you like to do?",
                "current_step": "greeting",
                "is_complete": False,
                "redirect_to_human": False
            }
    
    def _handle_booking_flow(self, user_input: str, current_step: str) -> Dict[str, Any]:
        """Handle appointment booking conversation flow."""
        flow = AGENT_CONFIG["intents"]["book_appointment"]["flow"]
        
        # Save data from current step
        if current_step in AGENT_CONFIG["data_collection"]:
            data_key = AGENT_CONFIG["data_collection"][current_step]["save_as"]
            self.collected_data[data_key] = user_input
            self._save_session()
        
        # Check for confirmation/rejection in confirmation step
        if current_step == "confirm_booking":
            if intent_detector.is_confirmation(user_input):
                # Booking confirmed
                return {
                    "response_text": AGENT_CONFIG["confirmation"]["script"].format(
                        date=self.collected_data.get("date", ""),
                        time=self.collected_data.get("time", "")
                    ) + " Your appointment is confirmed! " + AGENT_CONFIG["closing"],
                    "current_step": "booking_complete",
                    "is_complete": True,
                    "redirect_to_human": False,
                    "booking_confirmed": True
                }
            else:
                # User wants to change something
                self.session.current_step = "collect_date"
                self._save_session()
                return {
                    "response_text": "No problem. Let's pick a different time. What date would work better for you?",
                    "current_step": "collect_date",
                    "is_complete": False,
                    "redirect_to_human": False
                }
        
        # Move to next step
        try:
            current_idx = flow.index(current_step)
            if current_idx + 1 < len(flow):
                next_step = flow[current_idx + 1]
                self.session.current_step = next_step
                self._save_session()
                
                if next_step in AGENT_CONFIG["data_collection"]:
                    prompt = AGENT_CONFIG["data_collection"][next_step]["prompt"]
                    return {
                        "response_text": prompt,
                        "current_step": next_step,
                        "is_complete": False,
                        "redirect_to_human": False
                    }
                elif next_step == "confirm_booking":
                    # Present summary for confirmation
                    summary = self._build_booking_summary()
                    return {
                        "response_text": summary,
                        "current_step": next_step,
                        "is_complete": False,
                        "redirect_to_human": False
                    }
        except ValueError:
            pass
        
        return {
            "response_text": AGENT_CONFIG["fallback"]["complex"],
            "current_step": current_step,
            "is_complete": False,
            "redirect_to_human": True
        }
    
    def _handle_emergency_flow(self, user_input: str, current_step: str) -> Dict[str, Any]:
        """Handle emergency priority booking."""
        if current_step == "emergency_assess":
            # Collect basic info and offer immediate slot
            self.collected_data["reason"] = user_input
            self.collected_data["is_emergency"] = True
            self.session.current_step = "emergency_booking"
            self._save_session()
            
            return {
                "response_text": "I understand. For emergencies, I can get you in today or tomorrow. May I have your name and phone number so I can secure the earliest available slot?",
                "current_step": "emergency_booking",
                "is_complete": False,
                "redirect_to_human": False
            }
        
        elif current_step == "emergency_booking":
            # Extract name and phone from input
            self.collected_data["emergency_info"] = user_input
            self._save_session()
            
            return {
                "response_text": f"Thank you. I've noted this is urgent. Please come to our office at {AGENT_CONFIG.get('clinic_address', '123 Dental Ave')} as soon as possible. We're expecting you and will prioritize your care. {AGENT_CONFIG['closing']}",
                "current_step": "emergency_complete",
                "is_complete": True,
                "redirect_to_human": False,
                "is_emergency": True
            }
        
        return {
            "response_text": AGENT_CONFIG["fallback"]["complex"],
            "current_step": current_step,
            "is_complete": False,
            "redirect_to_human": True
        }
    
    def _handle_faq_flow(self, user_input: str, current_step: str) -> Dict[str, Any]:
        """Handle FAQ conversation flow."""
        # Check for another FAQ
        faq = intent_detector.match_faq(user_input)
        if faq:
            return {
                "response_text": faq["answer"] + " Anything else I can help with?",
                "current_step": "faq_followup",
                "is_complete": False,
                "redirect_to_human": False
            }
        
        # Check if user wants to book
        intent, _ = intent_detector.detect_intent(user_input)
        if intent == "book_appointment":
            self.session.intent = "book_appointment"
            self.session.current_step = "collect_name"
            self._save_session()
            return {
                "response_text": "I'd be happy to schedule that for you. " + AGENT_CONFIG["data_collection"]["collect_name"]["prompt"],
                "current_step": "collect_name",
                "is_complete": False,
                "redirect_to_human": False
            }
        
        # End FAQ session
        return {
            "response_text": AGENT_CONFIG["closing"],
            "current_step": "closing",
            "is_complete": True,
            "redirect_to_human": False
        }
    
    def _build_booking_summary(self) -> str:
        """Build booking confirmation summary."""
        name = self.collected_data.get("name", "")
        date = self.collected_data.get("date", "")
        time = self.collected_data.get("time", "")
        reason = self.collected_data.get("reason", "")
        
        return f"Let me confirm: Appointment for {name} on {date} at {time} for {reason}. Does this look correct?"
    
    def _handle_digit_input(self, digits: str) -> Dict[str, Any]:
        """Handle DTMF (button press) input."""
        # Map digits to actions if needed
        return {
            "response_text": "Thank you. Could you please say that instead?",
            "current_step": self.session.current_step,
            "is_complete": False,
            "redirect_to_human": False
        }
    
    def _no_input_response(self) -> Dict[str, Any]:
        """Handle no input from user."""
        return {
            "response_text": AGENT_CONFIG["fallback"]["no_input"],
            "current_step": self.session.current_step,
            "is_complete": False,
            "redirect_to_human": False
        }
    
    def get_collected_data(self) -> Dict[str, Any]:
        """Get all collected data from conversation."""
        return self.collected_data
    
    def close_session(self):
        """Mark session as inactive."""
        self.session.is_active = False
        db = next(get_db())
        db.commit()
