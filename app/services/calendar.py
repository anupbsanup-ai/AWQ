from datetime import datetime, date, time, timedelta
from typing import List, Dict, Optional, Tuple
import httpx
from app.config import get_settings

settings = get_settings()


class CalendarService:
    """Google Calendar integration for appointment management."""
    
    def __init__(self):
        self.calendar_id = settings.GOOGLE_CALENDAR_ID or "primary"
        self.clinic_open_hour = 8  # 8 AM
        self.clinic_close_hour = 18  # 6 PM
        self.appointment_duration = 30  # minutes
        
    async def check_availability(
        self, 
        check_date: date, 
        check_time: Optional[time] = None,
        preferred_range: Optional[str] = None
    ) -> Dict:
        """
        Check if a time slot is available.
        Returns availability status and alternative slots.
        """
        # Build potential time slots
        slots = self._generate_time_slots(check_date)
        
        # Filter by preferred time if specified
        if check_time:
            requested_slot = datetime.combine(check_date, check_time)
            is_available = await self._is_slot_available(requested_slot)
            
            if is_available:
                return {
                    "is_available": True,
                    "requested_slot": {
                        "date": check_date.isoformat(),
                        "time": check_time.strftime("%I:%M %p"),
                        "datetime": requested_slot.isoformat()
                    },
                    "alternative_slots": [],
                    "message": "The requested time slot is available."
                }
            else:
                # Find nearest alternatives
                alternatives = self._find_alternatives(check_date, check_time, slots)
                return {
                    "is_available": False,
                    "requested_slot": {
                        "date": check_date.isoformat(),
                        "time": check_time.strftime("%I:%M %p")
                    },
                    "alternative_slots": alternatives[:2],  # Suggest 2 nearest
                    "message": "That slot is not available. I have these nearby times."
                }
        
        # Return available slots for the day
        available_slots = []
        for slot in slots:
            if await self._is_slot_available(slot):
                available_slots.append({
                    "date": check_date.isoformat(),
                    "time": slot.strftime("%I:%M %p"),
                    "datetime": slot.isoformat()
                })
        
        # Filter by preferred range
        if preferred_range:
            available_slots = self._filter_by_range(available_slots, preferred_range)
        
        return {
            "is_available": len(available_slots) > 0,
            "requested_slot": None,
            "available_slots": available_slots[:5],  # Return up to 5 options
            "alternative_slots": [],
            "message": f"I found {len(available_slots)} available slots on {check_date.strftime('%A, %B %d')}."
        }
    
    def _generate_time_slots(self, slot_date: date) -> List[datetime]:
        """Generate all possible appointment time slots for a date."""
        slots = []
        current = datetime.combine(slot_date, time(self.clinic_open_hour, 0))
        end = datetime.combine(slot_date, time(self.clinic_close_hour, 0))
        
        while current < end:
            # Skip lunch break (12-1 PM)
            if not (12 <= current.hour < 13):
                slots.append(current)
            current += timedelta(minutes=self.appointment_duration)
        
        return slots
    
    def _filter_by_range(self, slots: List[Dict], preferred_range: str) -> List[Dict]:
        """Filter slots by preferred time range."""
        range_filters = {
            "morning": lambda h: 8 <= h < 12,
            "afternoon": lambda h: 13 <= h < 17,
            "evening": lambda h: 17 <= h < 19,
            "early": lambda h: 8 <= h < 10,
            "late": lambda h: 16 <= h < 19,
        }
        
        if preferred_range.lower() in range_filters:
            filter_fn = range_filters[preferred_range.lower()]
            return [s for s in slots if filter_fn(datetime.fromisoformat(s["datetime"]).hour)]
        
        return slots
    
    def _find_alternatives(self, check_date: date, check_time: time, all_slots: List[datetime]) -> List[Dict]:
        """Find the 2 closest alternative slots."""
        requested = datetime.combine(check_date, check_time)
        
        # Sort by time difference
        sorted_slots = sorted(all_slots, key=lambda s: abs((s - requested).total_seconds()))
        
        alternatives = []
        for slot in sorted_slots[:3]:
            if slot != requested:
                alternatives.append({
                    "date": check_date.isoformat(),
                    "time": slot.strftime("%I:%M %p"),
                    "datetime": slot.isoformat()
                })
        
        return alternatives[:2]
    
    async def _is_slot_available(self, slot_datetime: datetime) -> bool:
        """
        Check if a slot is available in Google Calendar.
        In production, this queries Google Calendar API.
        """
        # Simulated availability check
        # In production, call Google Calendar API:
        # - events.list with timeMin and timeMax
        # - Check for conflicts
        
        # For demo: block some random slots
        import hashlib
        hash_val = int(hashlib.md5(slot_datetime.isoformat().encode()).hexdigest(), 16)
        return hash_val % 3 != 0  # 2/3 of slots available
    
    async def book_appointment(
        self,
        name: str,
        phone: str,
        email: Optional[str],
        appointment_date: date,
        appointment_time: time,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Book an appointment in Google Calendar.
        Returns booking details including calendar event ID.
        """
        start_time = datetime.combine(appointment_date, appointment_time)
        end_time = start_time + timedelta(minutes=self.appointment_duration)
        
        event_data = {
            "summary": f"Appointment: {name}",
            "description": f"Patient: {name}\\nPhone: {phone}\\nEmail: {email or 'N/A'}\\nReason: {reason or 'General checkup'}",
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "America/Chicago"
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "America/Chicago"
            },
            "attendees": [{"email": email}] if email else [],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 1440},  # 1 day before
                    {"method": "sms", "minutes": 60}  # 1 hour before
                ]
            }
        }
        
        # In production, call Google Calendar API:
        # POST /calendar/v3/calendars/{calendarId}/events
        
        # Simulated response
        import hashlib
        event_id = hashlib.md5(f"{name}{start_time}".encode()).hexdigest()[:16]
        
        return {
            "success": True,
            "event_id": event_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "calendar_link": f"https://calendar.google.com/calendar/event?eid={event_id}"
        }
    
    async def cancel_appointment(self, event_id: str) -> bool:
        """Cancel an appointment in Google Calendar."""
        # In production: DELETE /calendar/v3/calendars/{calendarId}/events/{eventId}
        return True
    
    async def get_appointments_for_date(self, query_date: date) -> List[Dict]:
        """Get all appointments for a specific date."""
        # In production: Query Google Calendar API
        return []


calendar_service = CalendarService()
