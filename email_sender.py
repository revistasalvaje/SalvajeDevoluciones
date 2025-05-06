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
        
        logger.info(f"Email notification sent to {recipient_email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False
