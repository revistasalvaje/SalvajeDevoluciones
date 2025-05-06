import cv2
import numpy as np
import pytesseract
import logging
from config import OCR_LANG

logger = logging.getLogger(__name__)

def preprocess_image(image):
    """
    Preprocess the image for better OCR results
    
    Args:
        image: OpenCV image in BGR format
        
    Returns:
        Preprocessed image
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding to handle different lighting conditions
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY, 11, 2)
    
    # Apply morphological operations to remove noise
    kernel = np.ones((1, 1), np.uint8)
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    # Optional: Apply Gaussian blur to reduce noise further
    blurred = cv2.GaussianBlur(opening, (5, 5), 0)
    
    return blurred

def process_image_ocr(image):
    """
    Process the image using OCR to extract postal address
    
    Args:
        image: OpenCV image
        
    Returns:
        String containing the extracted postal address
    """
    try:
        # Preprocess the image
        preprocessed = preprocess_image(image)
        
        # Apply OCR using pytesseract
        custom_config = f'-l {OCR_LANG} --oem 3 --psm 6'
        text = pytesseract.image_to_string(preprocessed, config=custom_config)
        
        # Clean and format the extracted text
        cleaned_text = clean_ocr_text(text)
        
        logger.debug(f"Extracted text: {cleaned_text}")
        
        return cleaned_text
    except Exception as e:
        logger.error(f"Error in OCR processing: {str(e)}")
        return None

def clean_ocr_text(text):
    """
    Clean and format OCR extracted text
    
    Args:
        text: Raw OCR text
        
    Returns:
        Cleaned and formatted text
    """
    # Remove excessive newlines and whitespace
    cleaned = ' '.join(text.split())
    
    # Replace common OCR errors in Spanish addresses
    replacements = {
        '0': 'O',  # Sometimes 0 is misread as O
        'l': '1',  # Sometimes lowercase l is misread as 1
        '|': 'I',  # Sometimes | is misread as I
    }
    
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    
    return cleaned

def detect_address_region(image):
    """
    Attempt to detect the region of the image containing the address
    This is a more advanced function for better OCR results
    
    Args:
        image: OpenCV image
        
    Returns:
        Region of interest containing the address
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply binary thresholding
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Sort contours by area (largest first)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    # Get the bounding box of the largest contour
    if contours and len(contours) > 0:
        x, y, w, h = cv2.boundingRect(contours[0])
        # Extract region of interest
        roi = image[y:y+h, x:x+w]
        return roi
    
    # Fallback to the original image if no suitable contour is found
    return image
