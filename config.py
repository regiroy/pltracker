import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class QuickBooksConfig:
    """Configuration class for QuickBooks API settings"""

    # QuickBooks API credentials
    CLIENT_ID = os.getenv("QUICKBOOKS_CLIENT_ID")
    CLIENT_SECRET = os.getenv("QUICKBOOKS_CLIENT_SECRET")
    REDIRECT_URI = os.getenv("QUICKBOOKS_REDIRECT_URI", "http://localhost:8080/callback")

    # Environment
    ENVIRONMENT = os.getenv("QUICKBOOKS_ENVIRONMENT", "sandbox")  # 'sandbox' or 'production'

    # Data API base (for your resource calls, not OAuth)
    # Sandbox and prod have different API hosts
    if ENVIRONMENT == "sandbox":
        API_BASE_URL = "https://sandbox-quickbooks.api.intuit.com"
    else:
        API_BASE_URL = "https://quickbooks.api.intuit.com"

    # ----- OAuth endpoints (correct hosts) -----
    # UI for user consent:
    OAUTH_AUTH_HOST = "https://appcenter.intuit.com"
    OAUTH_AUTHORIZE_PATH = "/connect/oauth2"
    # Token endpoint:
    OAUTH_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

    # Scopes (space-delimited at request time)
    # Ensure your Intuit app actually has access to these
    SCOPES = [
        "com.intuit.quickbooks.accounting",
        # include these only if your app is entitled to them:
        # "com.intuit.quickbooks.payment",
        # "com.intuit.quickbooks.payroll",
        # Optional OIDC scopes if you want user info:
        # "openid", "profile", "email"
    ]

    # Data export
    EXPORT_FORMATS = ["csv", "excel", "json"]
    DEFAULT_EXPORT_FORMAT = "excel"

    # File paths
    OUTPUT_DIR = "exports"
    TOKEN_FILE = ".secrets/quickbooks_token.json"  # put secrets in a folder
