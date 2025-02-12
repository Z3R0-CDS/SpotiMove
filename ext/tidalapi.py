import os
import base64
import hashlib
import requests
import time
import json
from urllib.parse import urlencode

class TidalAPI:
    AUTH_URL = "https://login.tidal.com/authorize"
    TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
    API_BASE_URL = "https://api.tidal.com/v1"

    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0

    # Generate code verifier and code challenge (for PKCE)
    def _generate_code_verifier(self):
        code_verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b'=').decode('utf-8')
        code_challenge = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).rstrip(b'=').decode('utf-8')
        return code_verifier, code_challenge

    # Step 1: Redirect user to the OAuth authorization page
    def get_authorization_url(self):
        code_verifier, code_challenge = self._generate_code_verifier()
        self.code_verifier = code_verifier  # Store it for later use

        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'playlists.read',  # Adjust the scopes as necessary
            'code_challenge_method': 'S256',
            'code_challenge': code_challenge
        }
        auth_url = f"{self.AUTH_URL}?{urlencode(params)}"
        return auth_url

    # Step 2: Exchange authorization code for access token
    def fetch_access_token(self, authorization_code):
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'code': authorization_code,
            'redirect_uri': self.redirect_uri,
            'code_verifier': self.code_verifier
        }

        response = requests.post(self.TOKEN_URL, data=data)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data.get('refresh_token')
            self.token_expires_at = time.time() + token_data['expires_in']
            return token_data
        else:
            raise Exception(f"Error fetching access token: {response.text}")

    # Step 3: Use refresh token to get a new access token
    def refresh_access_token(self):
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'refresh_token': self.refresh_token
        }

        response = requests.post(self.TOKEN_URL, data=data)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_expires_at = time.time() + token_data['expires_in']
            return token_data
        else:
            raise Exception(f"Error refreshing access token: {response.text}")

    # Step 4: Make API requests
    def _make_request(self, method, endpoint, params=None):
        if time.time() >= self.token_expires_at:
            self.refresh_access_token()

        headers = {
            'Authorization': f"Bearer {self.access_token}"
        }

        url = f"{self.API_BASE_URL}{endpoint}"
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=params)
        else:
            raise Exception(f"Unsupported HTTP method: {method}")

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")

    # Step 5: Example method to get the user's playlists
    def get_user_playlists(self):
        return self._make_request('GET', '/users/me/playlists')

    # Step 6: Generic API request methods
    def get(self, endpoint, params=None):
        return self._make_request('GET', endpoint, params)

    def post(self, endpoint, data=None):
        return self._make_request('POST', endpoint, data)

# Usage Example:
if __name__ == '__main__':
    from config import ConfigHandle
    cfg = ConfigHandle()

    CLIENT_ID = cfg.get_item("TIDAL_CLIENT_ID")
    CLIENT_SECRET = cfg.get_item("TIDAL_CLIENT_SECRET")
    REDIRECT_URI = 'http://localhost:5000/callback'

    api = TidalAPI(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

    # Step 1: Get the authorization URL and print it
    print("Go to the following URL to authorize:")
    print(api.get_authorization_url())

    # After the user authorizes, they will be redirected to your redirect URI with a "code" parameter
    authorization_code = input("Enter the authorization code you received: ")

    # Step 2: Fetch the access token
    api.fetch_access_token(authorization_code)

    # Step 3: Fetch user playlists
    playlists = api.get_user_playlists()
    print(json.dumps(playlists, indent=2))
