import os
import logging
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import base64
import cv2
import numpy as np
import traceback

from ocr_utils import process_image_ocr
from address_matcher import find_matching_subscriber
from sheets_api import get_subscriber_data
from email_sender import send_notification_email

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database (even though we're not using it extensively in this app)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///ocr_app.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import the models here
    import models  # noqa: F401
    db.create_all()

@app.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html')

@app.route('/process-image', methods=['POST'])
def process_image():
    """Process the captured webcam image, extract address, find matching subscriber"""
    try:
        # Get image data from the request
        image_data = request.json.get('image')
        if not image_data:
            return jsonify({'error': 'No image data received'}), 400
        
        # Convert base64 image to OpenCV format
        encoded_data = image_data.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Process the image with OCR
        logger.debug("Processing image with OCR")
        extracted_address = process_image_ocr(img)
        if not extracted_address:
            return jsonify({'error': 'Could not extract any address from the image'}), 400
        
        # Get subscriber data from Google Sheets
        logger.debug("Fetching subscriber data from Google Sheets")
        subscribers = get_subscriber_data()
        if not subscribers:
            return jsonify({'error': 'Could not fetch subscriber data'}), 500
        
        # Find matching subscriber based on the extracted address
        logger.debug(f"Finding matching subscriber for address: {extracted_address}")
        matched_subscriber = find_matching_subscriber(extracted_address, subscribers)
        if not matched_subscriber:
            return jsonify({
                'status': 'not_found',
                'message': 'No matching subscriber found for the extracted address',
                'extracted_address': extracted_address
            })
        
        # Return the extracted address and matched subscriber for confirmation
        return jsonify({
            'status': 'match_found',
            'message': 'Se ha encontrado un suscriptor que coincide con la dirección',
            'subscriber': {
                'name': matched_subscriber.get('name', 'Subscriber'),
                'email': matched_subscriber.get('email', ''),
                'address': matched_subscriber.get('address', '')
            },
            'extracted_address': extracted_address
        })
    
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/manual-entry', methods=['POST'])
def manual_entry():
    """Process manually entered address data"""
    try:
        address_text = request.json.get('address')
        if not address_text:
            return jsonify({'error': 'No address provided'}), 400
        
        # Get subscriber data from Google Sheets
        subscribers = get_subscriber_data()
        if not subscribers:
            return jsonify({'error': 'Could not fetch subscriber data'}), 500
        
        # Find matching subscriber based on the address
        matched_subscriber = find_matching_subscriber(address_text, subscribers)
        if not matched_subscriber:
            return jsonify({
                'status': 'not_found',
                'message': 'No matching subscriber found for the provided address',
                'provided_address': address_text
            })
        
        # Return the extracted address and matched subscriber for confirmation
        return jsonify({
            'status': 'match_found',
            'message': 'Se ha encontrado un suscriptor que coincide con la dirección',
            'subscriber': {
                'name': matched_subscriber.get('name', 'Subscriber'),
                'email': matched_subscriber.get('email', ''),
                'address': matched_subscriber.get('address', '')
            },
            'extracted_address': address_text
        })
    
    except Exception as e:
        logger.error(f"Error processing manual entry: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('index.html'), 404

@app.route('/preview-email', methods=['POST'])
def preview_email():
    """Generate a preview of the email template with subscriber data"""
    try:
        # Get subscriber data from request
        subscriber_data = request.json.get('subscriber')
        if not subscriber_data:
            return jsonify({'error': 'No subscriber data provided'}), 400
        
        # Render the email template
        from email_sender import render_email_template
        email_html = render_email_template(subscriber_data)
        
        return jsonify({
            'status': 'success',
            'email_html': email_html
        })
    except Exception as e:
        logger.error(f"Error generating email preview: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/send-email', methods=['POST'])
def send_email():
    """Send notification email to the matched subscriber"""
    try:
        # Get subscriber data from request
        subscriber_data = request.json.get('subscriber')
        if not subscriber_data:
            return jsonify({'error': 'No subscriber data provided'}), 400
        
        # Send the notification email
        from email_sender import send_notification_email
        email_sent = send_notification_email(subscriber_data)
        
        # Save the processed mail entry in the database
        try:
            from models import ProcessedMail
            from datetime import datetime
            
            processed_mail = ProcessedMail(
                subscriber_email=subscriber_data.get('email', ''),
                extracted_address=request.json.get('extracted_address', ''),
                notification_sent=email_sent,
                processed_at=datetime.utcnow(),
                result_message='Email sent successfully' if email_sent else 'Failed to send email'
            )
            
            with app.app_context():
                db.session.add(processed_mail)
                db.session.commit()
                logger.info(f"Saved processed mail record for {subscriber_data.get('email', '')}")
        except Exception as db_error:
            logger.error(f"Error saving to database: {str(db_error)}")
        
        if email_sent:
            return jsonify({
                'status': 'success',
                'message': 'Email notification sent successfully',
                'subscriber': subscriber_data
            })
        else:
            return jsonify({
                'status': 'email_error',
                'message': 'Failed to send notification email',
                'subscriber': subscriber_data
            })
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {str(e)}")
    return render_template('index.html'), 500
