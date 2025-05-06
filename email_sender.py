import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
from config import SMTP_SERVER, SMTP_PORT, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_SUBJECT

logger = logging.getLogger(__name__)

def render_email_template(subscriber):
    """
    Render the email template with subscriber information
    
    Args:
        subscriber: Dictionary containing subscriber information
        
    Returns:
        Rendered HTML email content
    """
    # Load the template from the templates directory
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('email_template.html')
    
    # Render the template with subscriber data
    return template.render(
        name=subscriber.get('name', 'Suscriptor'),
        address=subscriber.get('address', ''),
        email=subscriber.get('email', '')
    )

def send_notification_email(subscriber):
    """
    Send notification email to the subscriber
    
    Args:
        subscriber: Dictionary containing subscriber information
        
    Returns:
        Boolean indicating whether the email was sent successfully
    """
    try:
        recipient_email = subscriber.get('email')
        if not recipient_email:
            logger.error("No recipient email provided")
            return False
        
        # Check if we're using SendGrid
        if os.environ.get('SENDGRID_API_KEY'):
            return send_email_via_sendgrid(subscriber, recipient_email)
        else:
            # Try SMTP if configurable
            if EMAIL_SENDER and EMAIL_PASSWORD and not EMAIL_SENDER.startswith('your-email'):
                return send_email_via_smtp(subscriber, recipient_email)
            else:
                # Demo mode - simulate successful email sending
                logger.info(f"DEMO MODE: Email would be sent to {recipient_email}")
                return True
    
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

def send_email_via_smtp(subscriber, recipient_email):
    """Send email using SMTP"""
    try:
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = EMAIL_SUBJECT
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient_email
        
        # Render the email content
        html_content = render_email_template(subscriber)
        
        # Attach HTML part
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email notification sent via SMTP to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"SMTP error: {str(e)}")
        return False

def send_email_via_sendgrid(subscriber, recipient_email):
    """Send email using SendGrid"""
    try:
        # Import SendGrid only when needed
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content
        
        # Get SendGrid API key
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logger.error("SendGrid API key not found")
            return False
        
        # Render email template
        html_content = render_email_template(subscriber)
        
        # Create message
        from_email = Email(EMAIL_SENDER if not EMAIL_SENDER.startswith('your-email') else "noreply@example.com")
        to_email = To(recipient_email)
        
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=EMAIL_SUBJECT,
            html_content=Content("text/html", html_content)
        )
        
        # Send email
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        logger.info(f"Email notification sent via SendGrid to {recipient_email}")
        return True
    
    except Exception as e:
        logger.error(f"SendGrid error: {str(e)}")
        return False
