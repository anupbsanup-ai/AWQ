"""
Voice service for handling Twilio calls and generating TwiML responses.
"""
from xml.etree.ElementTree import Element, tostring
from app.agent.config import AGENT_CONFIG


class VoiceService:
    """Generate TwiML for Twilio voice responses."""
    
    @staticmethod
    def create_twiml_response(message: str, gather_input: bool = True, action_url: str = "/voice/gather") -> str:
        """
        Create a TwiML response with voice output and optional input gathering.
        """
        response = Element("Response")
        
        # Add voice message
        say = Element("Say", {
            "voice": "Polly.Joanna",  # Professional female voice
            "language": "en-US"
        })
        say.text = message
        response.append(say)
        
        if gather_input:
            # Gather speech or DTMF input
            gather = Element("Gather", {
                "input": "speech dtmf",
                "action": action_url,
                "method": "POST",
                "speechTimeout": "auto",
                "timeout": "5",
                "numDigits": "1"
            })
            
            # Add a prompt for input
            prompt = Element("Say", {
                "voice": "Polly.Joanna",
                "language": "en-US"
            })
            prompt.text = "Please speak after the beep, or press a key."
            gather.append(prompt)
            
            response.append(gather)
            
            # Fallback if no input received
            redirect = Element("Redirect")
            redirect.text = "/voice/no-input"
            response.append(redirect)
        
        return tostring(response, encoding="unicode")
    
    @staticmethod
    def create_simple_response(message: str) -> str:
        """Create a simple TwiML response without input gathering."""
        response = Element("Response")
        
        say = Element("Say", {
            "voice": "Polly.Joanna",
            "language": "en-US"
        })
        say.text = message
        response.append(say)
        
        return tostring(response, encoding="unicode")
    
    @staticmethod
    def create_hangup_response(message: str) -> str:
        """Create a TwiML response that ends the call after speaking."""
        response = Element("Response")
        
        say = Element("Say", {
            "voice": "Polly.Joanna",
            "language": "en-US"
        })
        say.text = message
        response.append(say)
        
        hangup = Element("Hangup")
        response.append(hangup)
        
        return tostring(response, encoding="unicode")
    
    @staticmethod
    def create_transfer_response(message: str, transfer_number: str) -> str:
        """Create a TwiML response that transfers to a human agent."""
        response = Element("Response")
        
        say = Element("Say", {
            "voice": "Polly.Joanna",
            "language": "en-US"
        })
        say.text = message
        response.append(say)
        
        dial = Element("Dial")
        dial.text = transfer_number
        response.append(dial)
        
        return tostring(response, encoding="unicode")
    
    @staticmethod
    def create_play_beep() -> str:
        """Create a play element for beep sound."""
        return '<Play>http://api.twilio.com/cowbell.mp3</Play>'


voice_service = VoiceService()
