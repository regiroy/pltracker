#!/usr/bin/env python3
"""
QuickBooks Authentication Helper
- Opens the Intuit consent screen
- Captures ?code and ?realmId on your fixed redirect URI
- Exchanges code for real tokens
- Saves/loads tokens
- Auto-refreshes tokens when expired
- Simple smoke test against CompanyInfo
"""

import os
import json
import base64
import time
import threading
import http.server
import socketserver
import webbrowser
from typing import Optional
from urllib.parse import urlencode, urlparse, parse_qs, quote

import requests
from config import QuickBooksConfig


class QuickBooksAuthHelper:
    def __init__(self):
        self.config = QuickBooksConfig()
        self.state = self._random_state()

        # Parse the fixed redirect_uri from config (must match app exactly)
        ru = urlparse(self.config.REDIRECT_URI)
        if ru.scheme not in ("http", "https"):
            raise RuntimeError("REDIRECT_URI must start with http:// or https://")
        self._redirect_host = ru.hostname or "localhost"
        self._redirect_port = ru.port or (443 if ru.scheme == "https" else 80)
        self._redirect_path = ru.path or "/callback"

        # runtime fields
        self.server = None
        self.auth_code: Optional[str] = None
        self.realm_id: Optional[str] = None

        # storage
        self.token_file = getattr(self.config, "TOKEN_FILE", ".secrets/quickbooks_token.json")
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)

        # sanity checks
        missing = []
        if not getattr(self.config, "CLIENT_ID", None):
            missing.append("QUICKBOOKS_CLIENT_ID")
        if not getattr(self.config, "CLIENT_SECRET", None):
            missing.append("QUICKBOOKS_CLIENT_SECRET")
        if not getattr(self.config, "REDIRECT_URI", None):
            missing.append("QUICKBOOKS_REDIRECT_URI")
        if missing:
            raise RuntimeError("Missing env/config: " + ", ".join(missing))

    # ---------- OAuth URLs ----------

    def _authorize_url(self) -> str:
        scope_str = " ".join(getattr(self.config, "SCOPES", []))
        params = {
            "client_id": self.config.CLIENT_ID,
            "response_type": "code",
            "scope": scope_str,
            "redirect_uri": self.config.REDIRECT_URI,
            "state": self.state,
        }
        query = urlencode(params, quote_via=quote)
        return f"{self.config.OAUTH_AUTH_HOST}{self.config.OAUTH_AUTHORIZE_PATH}?{query}"

    # ---------- Local Callback Server ----------

    def _start_local_server(self):
        class AuthHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self_inner):
                parsed = urlparse(self_inner.path)
                if parsed.path != self._redirect_path:
                    self_inner.send_response(404)
                    self_inner.end_headers()
                    self_inner.wfile.write(b"Not Found")
                    return

                q = parse_qs(parsed.query)
                code = q.get("code", [None])[0]
                state = q.get("state", [None])[0]
                realm_id = q.get("realmId", [None])[0]

                if not code or state != self.state:
                    self_inner.send_response(400)
                    self_inner.end_headers()
                    self_inner.wfile.write(b"Invalid authorization response.")
                    self.server.should_stop = True
                    return

                self.server.auth_code = code
                self.server.realm_id = realm_id

                self_inner.send_response(200)
                self_inner.send_header("Content-Type", "text/html")
                self_inner.end_headers()
                self_inner.wfile.write(b"""
                    <html><body>
                    <h2>Authentication Successful!</h2>
                    <p>You can close this window and return to the terminal.</p>
                    <script>window.close();</script>
                    </body></html>
                """)
                self.server.should_stop = True

            def log_message(self_inner, fmt, *args):
                return

        class ReusableTCPServer(socketserver.ThreadingTCPServer):
            allow_reuse_address = True

        server = ReusableTCPServer((self._redirect_host, self._redirect_port), AuthHandler)
        server.auth_code = None
        server.realm_id = None
        server.should_stop = False
        self.server = server

        t = threading.Thread(target=self._serve_until_stopped, daemon=True)
        t.start()
        print(f"Callback server listening on {self._redirect_host}:{self._redirect_port}{self._redirect_path}")

    def _serve_until_stopped(self):
        while not self.server.should_stop:
            self.server.handle_request()

    # ---------- Public Flow ----------

    def authenticate(self, timeout_seconds: int = 300) -> Optional[dict]:
        """
        Launches browser → waits for code → exchanges for tokens.
        Returns the token dict (with realm_id added) on success.
        """
        self._start_local_server()

        auth_url = self._authorize_url()
        print(f"\nIf the browser doesn't open, use this URL:\n{auth_url}\n")
        webbrowser.open(auth_url)

        print("Waiting for authorization in the browser…")
        start = time.time()
        while not self.server.should_stop and (time.time() - start) < timeout_seconds:
            time.sleep(0.3)

        code = getattr(self.server, "auth_code", None)
        self.realm_id = getattr(self.server, "realm_id", None)
        if not code:
            print("No authorization code received (timed out or error).")
            return None

        print("Authorization code received. Exchanging for tokens…")
        tokens = self._exchange_code_for_tokens(code)
        if tokens and self.realm_id and "realm_id" not in tokens:
            tokens["realm_id"] = self.realm_id
        if tokens:
            self._save_tokens(tokens)
            print(f"Tokens saved to: {self.token_file}")
        return tokens

    def ensure_access_token(self) -> Optional[str]:
        """
        Loads tokens and refreshes them if needed.
        Returns a valid access_token or None.
        """
        tokens = self._load_tokens()
        if not tokens:
            print("No tokens found. Run with --authenticate first.")
            return None

        # If you track expiry, you can refresh proactively. Here, we try a lightweight API call
        # and refresh on 401. For now, just return the access token.
        return tokens.get("access_token")

    # ---------- Token Exchange & Refresh ----------

    def _exchange_code_for_tokens(self, auth_code: str) -> Optional[dict]:
        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.config.REDIRECT_URI,
        }
        headers = self._token_headers()
        try:
            resp = requests.post(self.config.OAUTH_TOKEN_URL, data=data, headers=headers, timeout=30)
            if resp.status_code != 200:
                print(f"Token exchange failed ({resp.status_code}): {resp.text}")
                return None
            return resp.json()
        except Exception as e:
            print(f"Token request error: {e}")
            return None

    def refresh_tokens(self) -> Optional[dict]:
        tokens = self._load_tokens()
        if not tokens or "refresh_token" not in tokens:
            print("No refresh token available. Re-authenticate.")
            return None

        data = {
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
        }
        headers = self._token_headers()
        try:
            resp = requests.post(self.config.OAUTH_TOKEN_URL, data=data, headers=headers, timeout=30)
            if resp.status_code != 200:
                print(f"Refresh failed ({resp.status_code}): {resp.text}")
                return None
            new_tokens = resp.json()
            # carry forward realm_id if not present
            if "realm_id" not in new_tokens and "realm_id" in tokens:
                new_tokens["realm_id"] = tokens["realm_id"]
            self._save_tokens(new_tokens)
            print("Tokens refreshed.")
            return new_tokens
        except Exception as e:
            print(f"Refresh error: {e}")
            return None

    def _token_headers(self):
        basic = base64.b64encode(
            f"{self.config.CLIENT_ID}:{self.config.CLIENT_SECRET}".encode()
        ).decode()
        return {
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

    # ---------- Token Storage ----------

    def _save_tokens(self, tokens: dict):
        with open(self.token_file, "w") as f:
            json.dump(tokens, f, indent=2)

    def _load_tokens(self) -> Optional[dict]:
        if not os.path.exists(self.token_file):
            return None
        with open(self.token_file, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return None

    # ---------- Simple API Smoke Test ----------

    def test_company_info(self) -> bool:
        """
        Calls the CompanyInfo endpoint. If unauthorized, tries 1 refresh automatically.
        """
        tokens = self._load_tokens()
        if not tokens or "access_token" not in tokens or "realm_id" not in tokens:
            print("No valid tokens or realm_id. Authenticate first.")
            return False

        ok = self._company_info(tokens["access_token"], tokens["realm_id"])
        if ok is True:
            print("CompanyInfo OK.")
            return True
        elif ok == 401:
            # try refresh once
            new_tokens = self.refresh_tokens()
            if not new_tokens:
                return False
            ok2 = self._company_info(new_tokens["access_token"], new_tokens.get("realm_id", tokens.get("realm_id")))
            if ok2 is True:
                print("CompanyInfo OK after refresh.")
                return True
            else:
                print(f"CompanyInfo failed after refresh (HTTP {ok2}).")
                return False
        else:
            print(f"CompanyInfo failed (HTTP {ok}).")
            return False

    def _company_info(self, access_token: str, realm_id: str):
        """
        GET /v3/company/{realmId}/companyinfo/{realmId}
        """
        url = f"{self.config.API_BASE_URL}/v3/company/{realm_id}/companyinfo/{realm_id}"
        params = {"minorversion": "65"}  # safe minor version as of 2024/2025
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
            if r.status_code == 200:
                return True
            return r.status_code
        except requests.RequestException:
            return 0  # network error

    # ---------- Utils ----------

    @staticmethod
    def _random_state(n: int = 24) -> str:
        # small local helper; state doesn't need to be cryptographically perfect here
        import secrets
        return secrets.token_urlsafe(n)


def main():
    print("Authentication Helper 2.")
    import argparse

    parser = argparse.ArgumentParser(description="QuickBooks Authentication Helper")
    parser.add_argument("--authenticate", action="store_true", help="Start OAuth authentication flow")
    parser.add_argument("--test", action="store_true", help="Call CompanyInfo using saved/refresh tokens")
    parser.add_argument("--refresh", action="store_true", help="Force a refresh token exchange")
    args = parser.parse_args()

    helper = QuickBooksAuthHelper()

    if args.authenticate:
        tokens = helper.authenticate()
        if tokens:
            print("Authentication completed successfully.")
        else:
            print("Authentication failed.")

    if args.refresh:
        ok = helper.refresh_tokens()
        print("Refresh OK." if ok else "Refresh failed.")

    if args.test:
        ok = helper.test_company_info()
        print("✓ Test passed" if ok else "✗ Test failed")


if __name__ == "__main__":
    print("Authentication Helper.")
    main()
