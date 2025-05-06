import re
import logging
from difflib import SequenceMatcher
import unicodedata

logger = logging.getLogger(__name__)

def normalize_text(text):
    """
    Normalize text by removing accents, converting to lowercase,
    and removing special characters
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove accents
    text = ''.join(c for c in unicodedata.normalize('NFD', text)
                  if unicodedata.category(c) != 'Mn')
    
    # Remove special characters and extra whitespace
    text = re.sub(r'[^\w\s]', ' ', text)
    text = ' '.join(text.split())
    
    return text

def extract_address_components(address):
    """
    Extract components from an address string
    
    Args:
        address: Address string
        
    Returns:
        Dictionary with address components
    """
    # Normalize the address first
    address = normalize_text(address)
    
    # Initialize components
    components = {
        'street': '',
        'number': '',
        'postal_code': '',
        'city': '',
        'province': ''
    }
    
    # Try to extract postal code (Spanish format: 5 digits)
    postal_code_match = re.search(r'\b\d{5}\b', address)
    if postal_code_match:
        components['postal_code'] = postal_code_match.group(0)
    
    # Try to extract street number
    number_match = re.search(r'\b(?:no|num|numero|nº)?\s*(\d+)\b', address)
    if number_match:
        components['number'] = number_match.group(1)
    
    # Extract other components based on Spanish address patterns
    # This is a simplified implementation and might need refinement
    
    return components

def calculate_address_similarity(address1, address2):
    """
    Calculate similarity between two addresses
    
    Args:
        address1: First address string
        address2: Second address string
        
    Returns:
        Similarity score between 0 and 1
    """
    # Normalize both addresses
    norm_addr1 = normalize_text(address1)
    norm_addr2 = normalize_text(address2)
    
    # Calculate similarity using SequenceMatcher
    matcher = SequenceMatcher(None, norm_addr1, norm_addr2)
    similarity = matcher.ratio()
    
    # Extract components and boost similarity if specific parts match
    comp1 = extract_address_components(address1)
    comp2 = extract_address_components(address2)
    
    # Boost score if postal codes match
    if comp1['postal_code'] and comp2['postal_code'] and comp1['postal_code'] == comp2['postal_code']:
        similarity += 0.2
    
    # Cap similarity at 1.0
    return min(similarity, 1.0)

def find_matching_subscriber(extracted_address, subscribers):
    """
    Find a matching subscriber based on the extracted address
    
    Args:
        extracted_address: Address extracted from OCR
        subscribers: List of subscriber dictionaries
        
    Returns:
        Matching subscriber dictionary or None if no match found
    """
    best_match = None
    best_similarity = 0.7  # Threshold for considering a match
    
    logger.debug(f"Looking for matches for address: {extracted_address}")
    
    for subscriber in subscribers:
        # Skip subscribers without address or email
        if not subscriber.get('address') or not subscriber.get('email'):
            continue
        
        # Calculate similarity between extracted address and subscriber address
        similarity = calculate_address_similarity(extracted_address, subscriber['address'])
        
        logger.debug(f"Similarity with {subscriber['address']}: {similarity}")
        
        # Update best match if similarity is higher
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = subscriber
    
    if best_match:
        logger.info(f"Found matching subscriber with score {best_similarity}: {best_match['email']}")
    else:
        logger.info("No matching subscriber found")
    
    return best_match
