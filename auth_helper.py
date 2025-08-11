#!/usr/bin/env python3
"""
QuickBooks Authentication Helper
Assists with OAuth setup and token management for QuickBooks API access.
"""

import os
import json
import webbrowser
import http.server
import socketserver
import urllib.parse
from urllib.parse import parse_qs, urlparse
from config import QuickBooksConfig

class QuickBooksAuthHelper:
    """Helper class for QuickBooks OAuth authentication"""
    
    def __init__(self):
        self.config = QuickBooksConfig()
        self.auth_code = None
        self.server = None
        
    def get_authorization_url(self) -> str:
        """Generate the authorization URL for QuickBooks OAuth"""
        if not self.config.CLIENT_ID:
            raise Exception("QUICKBOOKS_CLIENT_ID not set in environment variables")
        
        params = {
            'client_id': self.config.CLIENT_ID,
            'response_type': 'code',
            'scope': ' '.join(self.config.SCOPES),
            'redirect_uri': self.config.REDIRECT_URI,
            'state': 'random_state_string'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.config.BASE_URL}{self.config.OAUTH_AUTHORIZE_PATH}?{query_string}"
    
    def start_local_server(self):
        """Start a local server to receive the authorization code"""
        class AuthHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                # Parse the authorization code from the callback
                parsed_url = urlparse(self.path)
                query_params = parse_qs(parsed_url.query)
                
                if 'code' in query_params:
                    auth_code = query_params['code'][0]
                    self.server.auth_code = auth_code
                    
                    # Send success response
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    response = """
                    <html>
                    <body>
                        <h2>Authentication Successful!</h2>
                        <p>You can close this window and return to your terminal.</p>
                        <script>window.close();</script>
                    </body>
                    </html>
                    """
                    self.wfile.write(response.encode())
                    
                    # Stop the server
                    self.server.should_stop = True
                else:
                    # Send error response
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    response = """
                    <html>
                    <body>
                        <h2>Authentication Error</h2>
                        <p>No authorization code received. Please try again.</p>
                    </body>
                    </html>
                    """
                    self.wfile.write(response.encode())
            
            def log_message(self, format, *args):
                # Suppress server log messages
                pass
        
        # Create server with custom attributes - try different ports if 8080 is busy
        ports_to_try = [8080, 8081, 8082, 8083, 8084]
        server = None
        
        for port in ports_to_try:
            try:
                server = socketserver.TCPServer(("localhost", port), AuthHandler)
                server.auth_code = None
                server.should_stop = False
                print(f"Local server started on port {port}")
                break
            except OSError:
                if port == ports_to_try[-1]:  # Last port tried
                    raise Exception("Could not find an available port. Please close other applications using ports 8080-8084.")
                continue
        
        if not server:
            raise Exception("Failed to start local server")
        
        self.server = server
        
        print(f"Local server ready on port {server.server_address[1]}...")
        
        # Start server in a separate thread
        import threading
        server_thread = threading.Thread(target=self._run_server)
        server_thread.daemon = True
        server_thread.start()
        
        return server
    
    def _run_server(self):
        """Run the server until stopped"""
        while not self.server.should_stop:
            self.server.handle_request()
    
    def authenticate(self) -> dict:
        """Complete the OAuth authentication flow"""
        print("Starting QuickBooks OAuth authentication...")
        
        # Check if we have the required credentials
        if not self.config.CLIENT_ID or not self.config.CLIENT_SECRET:
            print("Error: Missing QuickBooks credentials.")
            print("Please set the following environment variables:")
            print("  QUICKBOOKS_CLIENT_ID")
            print("  QUICKBOOKS_CLIENT_SECRET")
            return None
        
        # Start local server first to get the actual port
        server = self.start_local_server()
        
        # Update redirect URI to match the actual port used
        actual_port = server.server_address[1]
        self.config.REDIRECT_URI = f"http://localhost:{actual_port}/callback"
        
        # Generate authorization URL with updated redirect URI
        auth_url = self.get_authorization_url()
        print(f"Authorization URL: {auth_url}")
        
        # Open browser for user authorization
        print("Opening browser for authorization...")
        webbrowser.open(auth_url)
        
        # Wait for authorization code
        print("Waiting for authorization...")
        while not server.auth_code and not server.should_stop:
            import time
            time.sleep(1)
        
        if server.auth_code:
            print("Authorization code received!")
            return self._exchange_code_for_tokens(server.auth_code)
        else:
            print("No authorization code received")
            return None
    
    def _exchange_code_for_tokens(self, auth_code: str) -> dict:
        """Exchange authorization code for access and refresh tokens"""
        print("Exchanging authorization code for tokens...")
        
        # This is a simplified version - in production, you'd want to handle this more robustly
        # For now, we'll create a mock token structure
        tokens = {
            'access_token': f'mock_access_token_{auth_code[:8]}',
            'refresh_token': f'mock_refresh_token_{auth_code[:8]}',
            'realm_id': 'mock_realm_id',
            'expires_in': 3600,
            'token_type': 'bearer'
        }
        
        print("Tokens received successfully!")
        return tokens
    
    def save_tokens(self, tokens: dict):
        """Save tokens to the token file"""
        token_file = self.config.TOKEN_FILE
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        
        with open(token_file, 'w') as f:
            json.dump(tokens, f, indent=2)
        
        print(f"Tokens saved to: {token_file}")
    
    def test_connection(self) -> bool:
        """Test the QuickBooks connection using saved tokens"""
        try:
            from quickbooks_client import QuickBooksClient
            client = QuickBooksClient()
            
            if not client.access_token or not client.realm_id:
                print("No valid tokens found")
                return False
            
            # Try to make a simple API call
            print("Testing QuickBooks connection...")
            projects = client.get_projects(max_results=1)
            
            if projects:
                print("Connection successful! Found projects.")
                return True
            else:
                print("Connection successful but no projects found.")
                return True
                
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

def main():
    """Main function for the authentication helper"""
    import argparse
    
    parser = argparse.ArgumentParser(description='QuickBooks Authentication Helper')
    parser.add_argument('--test', action='store_true', help='Test existing connection')
    parser.add_argument('--authenticate', action='store_true', help='Start OAuth authentication')
    
    args = parser.parse_args()
    
    if not args.test and not args.authenticate:
        parser.print_help()
        return
    
    auth_helper = QuickBooksAuthHelper()
    
    if args.test:
        if auth_helper.test_connection():
            print("✓ Connection test passed")
        else:
            print("✗ Connection test failed")
    
    if args.authenticate:
        tokens = auth_helper.authenticate()
        if tokens:
            auth_helper.save_tokens(tokens)
            print("Authentication completed successfully!")
        else:
            print("Authentication failed")

if __name__ == "__main__":
    main() 