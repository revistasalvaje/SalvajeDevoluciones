from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    
class ProcessedMail(db.Model):
    """Model to store logs of processed returned mail"""
    id = db.Column(db.Integer, primary_key=True)
    subscriber_email = db.Column(db.String(120), nullable=False)
    extracted_address = db.Column(db.Text, nullable=False)
    notification_sent = db.Column(db.Boolean, default=False)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    result_message = db.Column(db.Text)
