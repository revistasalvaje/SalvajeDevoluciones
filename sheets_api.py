import os
import gspread
import logging
from oauth2client.service_account import ServiceAccountCredentials
from config import SHEET_URL, SHEET_ID, WORKSHEET_NAME

logger = logging.getLogger(__name__)

def get_google_sheets_client():
    """
    Get authenticated Google Sheets client
    
    Returns:
        Authenticated gspread client or None if authentication fails
    """
    try:
        # Use service account credentials from environment or file
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # Check if credentials exist as environment variable
        if os.environ.get('GOOGLE_CREDENTIALS'):
            import json
            import tempfile
            
            # Create temporary file with credentials
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp:
                temp.write(os.environ.get('GOOGLE_CREDENTIALS'))
                temp_path = temp.name
            
            credentials = ServiceAccountCredentials.from_json_keyfile_name(temp_path, scope)
            os.unlink(temp_path)  # Remove temporary file
        else:
            # Look for credentials file
            credentials_path = os.environ.get('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
            credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        
        client = gspread.authorize(credentials)
        return client
    
    except Exception as e:
        logger.error(f"Error authenticating with Google Sheets: {str(e)}")
        return None

def get_subscriber_data():
    """
    Get subscriber data from Google Sheets
    
    Returns:
        List of dictionaries containing subscriber data
    """
    try:
        client = get_google_sheets_client()
        if not client:
            logger.warning("Could not get Google Sheets client. Using demo data.")
            return get_demo_subscriber_data()
        
        # Open the spreadsheet and worksheet
        sheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
        
        # Get all data as list of dictionaries
        data = sheet.get_all_records()
        
        # Assuming the sheet has columns: name, email, address, etc.
        subscribers = []
        for row in data:
            # Skip rows without essential information
            if not row.get('email') or not row.get('address'):
                continue
                
            subscriber = {
                'name': row.get('name', ''),
                'email': row.get('email', ''),
                'address': row.get('address', ''),
                'city': row.get('city', ''),
                'postal_code': row.get('postal_code', '')
            }
            subscribers.append(subscriber)
        
        logger.info(f"Loaded {len(subscribers)} subscribers from Google Sheets")
        return subscribers
    
    except Exception as e:
        logger.error(f"Error fetching subscriber data: {str(e)}")
        logger.info("Using demo subscriber data instead")
        return get_demo_subscriber_data()

def get_demo_subscriber_data():
    """
    Get demo subscriber data when Google Sheets is not available
    
    Returns:
        List of dictionaries containing demo subscriber data
    """
    logger.info("Loading demo subscriber data")
    
    # Demo data for testing the application
    demo_subscribers = [
        {
            'name': 'María García',
            'email': 'demo_maria@example.com',
            'address': 'Calle Gran Vía 31, 28013 Madrid',
            'city': 'Madrid',
            'postal_code': '28013'
        },
        {
            'name': 'Juan Rodríguez',
            'email': 'demo_juan@example.com',
            'address': 'Avda. Diagonal 423, 08036 Barcelona',
            'city': 'Barcelona',
            'postal_code': '08036'
        },
        {
            'name': 'Carmen López',
            'email': 'demo_carmen@example.com',
            'address': 'Plaza Nueva 15, 41001 Sevilla',
            'city': 'Sevilla',
            'postal_code': '41001'
        },
        {
            'name': 'José Martínez',
            'email': 'demo_jose@example.com',
            'address': 'Calle Triana 45, 35002 Las Palmas',
            'city': 'Las Palmas',
            'postal_code': '35002'
        },
        {
            'name': 'Ana Fernández',
            'email': 'demo_ana@example.com',
            'address': 'Avenida de la Constitución 12, 46001 Valencia',
            'city': 'Valencia',
            'postal_code': '46001'
        }
    ]
    
    logger.info(f"Loaded {len(demo_subscribers)} demo subscribers")
    return demo_subscribers
