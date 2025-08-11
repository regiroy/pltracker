import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class QuickBooksConfig:
    """Configuration class for QuickBooks API settings"""
    
    # QuickBooks API credentials
    CLIENT_ID = os.getenv('QUICKBOOKS_CLIENT_ID')
    CLIENT_SECRET = os.getenv('QUICKBOOKS_CLIENT_SECRET')
    REDIRECT_URI = os.getenv('QUICKBOOKS_REDIRECT_URI', 'http://localhost:8080/callback')
    
    # Environment detection
    ENVIRONMENT = os.getenv('QUICKBOOKS_ENVIRONMENT', 'sandbox')  # 'sandbox' or 'production'
    
    # QuickBooks API endpoints
    BASE_URL = "https://sandbox.qbo.intuit.com/"  # Same for both sandbox and production
    if ENVIRONMENT == "sandbox":
        API_BASE_URL = "https://sandbox.qbo.intuit.com/"
    else:
        API_BASE_URL = "https://quickbooks.api.intuit.com"
    
    # OAuth endpoint paths
    OAUTH_AUTHORIZE_PATH = '/connect/oauth2'  # OAuth endpoint
    OAUTH_TOKEN_PATH = '/connect/oauth2/token'  # Token endpoint
    
    # Scopes needed for reading projects and expenses
    SCOPES = [
        'com.intuit.quickbooks.accounting',
        'com.intuit.quickbooks.payment',
        'com.intuit.quickbooks.payroll'
    ]
    
    # Data export settings
    EXPORT_FORMATS = ['csv', 'excel', 'json']
    DEFAULT_EXPORT_FORMAT = 'excel'
    
    # File paths
    OUTPUT_DIR = 'exports'
    TOKEN_FILE = 'quickbooks_token.json' 