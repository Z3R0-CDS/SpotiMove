## THIS IS ONLY FIRST ATTEMPTS TO ACCESS TIDALs API
## SAVED IN CASE IT COULD BE NEEDED AS IT TOOK ALOT OF RESEARCH
## DO NOT USE IN ANY CASE! UNLESS OTHERWISE STATED

import os
import base64
import hashlib
import requests
import time
import json
from urllib.parse import urlencode
from typing import Any, Dict
import random

# PLAYLST CREATION LEGACY CODE

# api_v2_location = "https://api.tidal.com/v2"
# TIDAL_API_URL = "https://openapi.tidal.com/v2"
# TIDAL_AUTH_URL = "https://login.tidal.com/authorize"
# TIDAL_TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"

# playlist = sp.playlist(playlist)
# print(playlist)
# songs = sp.playlist_items(playlist['id'])
# # my-collection/playlists/folders/create-playlist
# # https://listen.tidal.com/v2/suggestions/?countryCode=DE&locale=en_US&deviceType=BROWSER&explicit=true&hybrid=true&query=test12
#
# access_token = session.get("tidal_token", {}).get("access_token")
# if not access_token:
#     return {"error": "Not logged into Tidal"}, 401
# headers = {"Authorization": f"Bearer {access_token}"}
# playlists_url = f"{api_v2_location}/my-collection/playlists/folders/create-playlist"
# # playlists_url = "https://listen.tidal.com/v2/my-collection/playlists/folders?folderId=root"
# params = {"name": playlist['name'], "description": "None", "folderId": "root"}
# response = requests.get(playlists_url, headers=headers, params=params)
# if response.status_code == 200:
#     print(response.json())
#     return response.json()
# else:
#     print(f"Failed to create playlist:({response.status_code}) {response.text} ")
#     return {"error": response.json()}, response.status_code


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



# Data Models

JsonObj = Dict[str, Any]



class LinkLogin:
    """The data required for logging in to TIDAL using a remote link, json is the data
    returned from TIDAL."""

    #: Number of seconds until the code expires
    expires_in: int
    #: The code the user should enter at the uri
    user_code: str
    #: The link the user has to visit
    verification_uri: str
    #: The link the user has to visit, with the code already included
    verification_uri_complete: str
    #: After how much time the uri expires.
    expires_in: float
    #: The interval for authorization checks against the backend.
    interval: float
    #: The unique device code necessary for authorization.
    device_code: str

    def __init__(self, json: JsonObj):
        self.expires_in = int(json["expiresIn"])
        self.user_code = str(json["userCode"])
        self.verification_uri = str(json["verificationUri"])
        self.verification_uri_complete = str(json["verificationUriComplete"])
        self.expires_in = float(json["expiresIn"])
        self.interval = float(json["interval"])
        self.device_code = str(json["deviceCode"])


## Tidal API Interfaces

class TidalDeviceAPI:
    AUTH_URL = "https://login.tidal.com/authorize"
    TOKEN_URL = "https://auth.tidal.com/v1/oauth2/device_authorization"
    API_BASE_URL = "https://api.tidal.com/v1"

    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.request_session = requests.Session()

    def get_authorization_url(self):
        """Return information required to login into TIDAL using a device authorization
        link.

        :return: Login information for device authorization retrieved from the TIDAL backend.
        :rtype: :class:`LinkLogin`
        """
        url = "https://auth.tidal.com/v1/oauth2/device_authorization"
        params = {"client_id": self.client_id, "scope": "r_usr w_usr w_sub"}

        request = self.request_session.post(url, params)

        if not request.ok:
            print("Login failed: %s", request.text)
            request.raise_for_status()

        json = request.json()

        return LinkLogin(json)



class TidalDeviceAuth:
    DEVICE_CODE_URL = "https://auth.tidal.com/v1/oauth2/device_authorization"
    TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
    API_URL = "https://api.tidal.com/v1"

    def __init__(self, client_id):
        self.client_id = client_id
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0
        self.device_code = None
        self.interval = 5

    def start_device_login(self):
        """Step 1: Request a device code"""
        data = {
            "client_id": self.client_id,
            "scope": "r_usr w_usr"
        }
        resp = requests.post(self.DEVICE_CODE_URL, data=data).json()
        print(json.dumps(resp, indent=2))

        self.device_code = resp["device_code"]
        self.interval = resp["interval"]

        return {
            "verification_uri": resp["verification_uri"],
            "user_code": resp["user_code"],
            "expires_in": resp["expires_in"]
        }

    def poll_for_token(self):
        """Step 2: Poll until the user logs in"""
        while True:
            time.sleep(self.interval)
            data = {
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": self.device_code,
                "client_id": self.client_id,
            }
            response = requests.post(self.TOKEN_URL, data=data)

            if response.status_code == 200:
                token = response.json()
                self.access_token = token["access_token"]
                self.refresh_token = token.get("refresh_token")
                self.token_expires_at = time.time() + token["expires_in"]
                return token

            error = response.json().get("error")

            if error == "authorization_pending":
                continue
            if error == "slow_down":
                self.interval += 2
                continue
            else:
                raise Exception(f"TIDAL device login failed: {error}")

    def get(self, endpoint, params=None):
        """Simple GET request with auto-refresh"""
        if time.time() >= self.token_expires_at:
            self.refresh()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = self.API_URL + endpoint
        r = requests.get(url, params=params, headers=headers)

        if r.status_code != 200:
            raise Exception(r.text)
        return r.json()

    def refresh(self):
        """Refresh access token"""
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": self.refresh_token
        }
        r = requests.post(self.TOKEN_URL, data=data).json()
        self.access_token = r["access_token"]
        self.token_expires_at = time.time() + r["expires_in"]



class LGTidalAPI:
    AUTH_URL = "https://login.tidal.com/authorize"
    TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
    API_BASE_URL = "https://openapi.tidal.com"

    SCOPES = "r_usr+w_usr+w_sub"
    # "playlists.read user.read" user.read collection.read playlists.write collection.write

    def __init__(self, client_id, redirect_uri, client_secret=None):
        self.client_id = client_id
        self.client_secret = client_secret  # optional (TIDAL PKCE benötigt kein secret)
        self.redirect_uri = redirect_uri

        self.code_verifier = None
        self.access_token = None
        self.refresh_token = None
        self.expires_at = 0
        self.user_id = None

    # ----------------------------------------------------------
    # PKCE
    # ----------------------------------------------------------
    def _generate_pkce(self):
        code_verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b"=").decode()
        code_challenge = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).rstrip(b"=").decode()
        return code_verifier, code_challenge

    # ----------------------------------------------------------
    # LOGIN URL GENERIEREN
    # ----------------------------------------------------------
    def get_login_url(self):
        self.code_verifier, code_challenge = self._generate_pkce()

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "scope": self.SCOPES
        }

        return f"{self.AUTH_URL}?{urlencode(params)}"

    # ----------------------------------------------------------
    # ACCESS TOKEN HOLEN
    # ----------------------------------------------------------
    def fetch_token(self, code):
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code_verifier": self.code_verifier,
            "code": code,
            "client_unique_key": format(random.getrandbits(64), "02x")
        }

        resp = requests.post(self.TOKEN_URL, data=data)
        if resp.status_code != 200:
            raise Exception(f"TIDAL auth error: {resp.text}")

        token = resp.json()
        self.access_token = token["access_token"]
        self.refresh_token = token.get("refresh_token")
        self.expires_at = time.time() + token["expires_in"]

        # user-id laden
        me = self.get("/users/me")
        self.user_id = me["userId"]

        return token

    # ----------------------------------------------------------
    # TOKEN REFRESH
    # ----------------------------------------------------------
    def refresh(self):
        if not self.refresh_token:
            raise Exception("No refresh token available.")

        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": self.refresh_token
        }

        resp = requests.post(self.TOKEN_URL, data=data)
        if resp.status_code != 200:
            raise Exception(f"TIDAL refresh error: {resp.text}")

        token = resp.json()
        self.access_token = token["access_token"]
        self.expires_at = time.time() + token["expires_in"]

    # ----------------------------------------------------------
    # GENERIC REQUEST WRAPPER
    # ----------------------------------------------------------
    def _ensure_token(self):
        if time.time() > self.expires_at:
            self.refresh()

    def _request(self, method, endpoint, params=None, data=None):
        self._ensure_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        url = f"{self.API_BASE_URL}{endpoint}"

        r = requests.request(method, url, headers=headers, params=params, json=data)
        if r.status_code not in (200, 201):
            raise Exception(f"TIDAL API error: {r.status_code}: {r.text}")

        return r.json()

    def get(self, endpoint, params=None):
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint, data=None):
        return self._request("POST", endpoint, data=data)

    # ----------------------------------------------------------
    # PLAYLIST-FUNKTIONEN
    # ----------------------------------------------------------
    def get_user_playlists(self):
        return self.get(f"/users/{self.user_id}/playlists")

    def create_playlist(self, title, description=""):
        payload = {
            "title": title,
            "description": description
        }
        return self.post("/playlists", payload)

    def add_tracks_to_playlist(self, playlist_id, track_ids: list):
        payload = {
            "trackIds": track_ids
        }
        return self.post(f"/playlists/{playlist_id}/items", payload)

    def get_playlist_items(self, playlist_id):
        return self.get(f"/playlists/{playlist_id}/items")

    def get_track(self, track_id):
        return self.get(f"/tracks/{track_id}")


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
