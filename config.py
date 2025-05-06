import os

# OCR Configuration
OCR_LANG = "spa"  # Spanish language for Tesseract OCR

# Google Sheets Configuration
SHEET_URL = "https://docs.google.com/spreadsheets/d/1X30rUyIiKk3MY2DxFxqrJlJ0WZcqgo0aTnKhPOnZQPc/edit?usp=sharing"
SHEET_ID = "1X30rUyIiKk3MY2DxFxqrJlJ0WZcqgo0aTnKhPOnZQPc"
WORKSHEET_NAME = "subscribers"  # Assuming this is the name of the worksheet

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "your-email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-app-password")

# Email Template
EMAIL_SUBJECT = "Problema con tu envío de revista"
