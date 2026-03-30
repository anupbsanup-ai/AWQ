from typing import Optional, Dict
import httpx
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.config import get_settings

settings = get_settings()


class NotificationService:
    """Handle SMS and Email notifications."""
    
    def __init__(self):
        self.sendgrid_client = None
        if settings.SENDGRID_API_KEY:
            self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
    
    async def send_sms(self, to: str, message: str) -> bool:
        """
        Send SMS notification using Twilio.
        Returns True if sent successfully.
        """
        try:
            from twilio.rest import Client
            
            if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
                print(f"[SMS SIMULATION] To: {to}, Message: {message}")
                return True
            
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            message = client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=to
            )
            
            return message.sid is not None
        except Exception as e:
            print(f"SMS sending error: {e}")
            return False
    
    async def send_email(
        self, 
        to: str, 
        subject: str, 
        body: str, 
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send email notification using SendGrid.
        Returns True if sent successfully.
        """
        try:
            if not self.sendgrid_client:
                print(f"[EMAIL SIMULATION] To: {to}, Subject: {subject}")
                print(f"Body: {body}")
                return True
            
            message = Mail(
                from_email=settings.CLINIC_EMAIL,
                to_emails=to,
                subject=subject,
                plain_text_content=body,
                html_content=html_body
            )
            
            response = self.sendgrid_client.send(message)
            return response.status_code in [200, 202]
        except Exception as e:
            print(f"Email sending error: {e}")
            return False
    
    async def send_appointment_confirmation(
        self,
        phone: str,
        email: Optional[str],
        name: str,
        appointment_date: str,
        appointment_time: str,
        clinic_name: str = "Chicago Dental 312"
    ) -> Dict:
        """
        Send appointment confirmation via SMS and email.
        """
        # SMS Message
        sms_message = (
            f"Hi {name}, your appointment at {clinic_name} is confirmed for "
            f"{appointment_date} at {appointment_time}. "
            f"Reply CONFIRM to verify or CANCEL to reschedule."
        )
        
        # Email content
        email_subject = f"Appointment Confirmation - {clinic_name}"
        email_body = f"""
Dear {name},

Your appointment has been confirmed:

Date: {appointment_date}
Time: {appointment_time}
Clinic: {clinic_name}
Address: {settings.CLINIC_ADDRESS}

If you need to reschedule, please call us at {settings.CLINIC_PHONE} or reply to this email.

We look forward to seeing you!

Best regards,
{clinic_name} Team
        """
        
        email_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0;">Appointment Confirmation</h2>
                <p>Dear {name},</p>
                <p>Your appointment has been confirmed:</p>
                <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Date:</strong> {appointment_date}</p>
                    <p><strong>Time:</strong> {appointment_time}</p>
                    <p><strong>Clinic:</strong> {clinic_name}</p>
                    <p><strong>Address:</strong> {settings.CLINIC_ADDRESS}</p>
                </div>
                <p>If you need to reschedule, please call us at {settings.CLINIC_PHONE} or reply to this email.</p>
                <p>We look forward to seeing you!</p>
                <p>Best regards,<br>{clinic_name} Team</p>
            </div>
        </body>
        </html>
        """
        
        # Send notifications
        sms_sent = await self.send_sms(phone, sms_message)
        email_sent = False
        if email:
            email_sent = await self.send_email(email, email_subject, email_body, email_html)
        
        return {
            "sms_sent": sms_sent,
            "email_sent": email_sent,
            "sms_message": sms_message,
            "email_subject": email_subject
        }
    
    async def send_appointment_reminder(
        self,
        phone: str,
        email: Optional[str],
        name: str,
        appointment_date: str,
        appointment_time: str
    ) -> Dict:
        """Send appointment reminder (typically 24 hours before)."""
        sms_message = (
            f"Reminder: Hi {name}, you have an appointment at Chicago Dental 312 "
            f"tomorrow ({appointment_date}) at {appointment_time}. See you then!"
        )
        
        email_subject = "Appointment Reminder - Chicago Dental 312"
        email_body = f"""
Dear {name},

This is a friendly reminder about your upcoming appointment:

Tomorrow, {appointment_date} at {appointment_time}

We look forward to seeing you!

Chicago Dental 312
        """
        
        sms_sent = await self.send_sms(phone, sms_message)
        email_sent = await self.send_email(email, email_subject, email_body) if email else False
        
        return {
            "sms_sent": sms_sent,
            "email_sent": email_sent
        }


notification_service = NotificationService()
