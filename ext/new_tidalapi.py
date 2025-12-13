# =============================================================================
#  Copyright (c) 2025 Zero Industries
#  https://zero-industries.com
#
#  This software is NOT free for corporate use.
#
#  Permission is granted to individuals for open-source, educational, or
#  non-commercial use only.
#
#  Any commercial, enterprise, or profit-oriented use — including internal
#  tooling at a company — requires a paid license from Zero Industries.
#
#  Unauthorized corporate use is strictly prohibited.
#
#  PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND.
#
# =============================================================================


import os
import time
import base64
import hashlib
import requests
from urllib.parse import urlencode
import json
from dataclasses import dataclass, is_dataclass


@dataclass
class TidalUser:
    id: str
    username: str
    country: str
    email: str

    def __init__(self, data: dict):
        # TIDAL shape
        self.id = str(data.get("id"))
        self.username = data['attributes']['username']
        self.country = data['attributes']['country']
        self.email = data['attributes']['email']

@dataclass
class TidalArtist:
    id: str
    username: str
    country: str

@dataclass
class TidalSong:
    id: str
    name: str
    artist: str
    copyright: str = None
    explicit: bool = False

    def __init__(self, data: dict):
        # TIDAL shape
        error = 'No attribute loaded'
        attributes = data.get('attributes', {})
        self.id = data['id']
        self.name = attributes.get('title', error)
        if 'copyright' in attributes:
            self.copyright = attributes['copyright']['text']
        self.artist = "Coming soon!"
        self.explicit = attributes.get('explicit', False)

@dataclass
class TidalPlaylist:
    id: str
    name: str
    songs: list[TidalSong]
    created_at: str

    def __init__(self, data: dict, songs: list[TidalSong]=[]):
        # TIDAL shape
        attributes = data['attributes']
        self.id = data['id']
        self.name = attributes['name']
        self.songs = songs
        self.created_at = attributes['createdAt']

    def to_dict(self):
        def serialize(obj):
            if is_dataclass(obj):
                return {k: serialize(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [serialize(i) for i in obj]
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            else:
                return obj

        return serialize(self)

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False)

class TidalAPI:
    AUTH_URL = "https://login.tidal.com/authorize"
    TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
    API_BASE = "https://openapi.tidal.com/v2"  # v1 endpoints for user data

    SCOPES = "playlists.read playlists.write user.read collection.read collection.write"

    def __init__(self, client_id, redirect_uri):
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.code_verifier = None
        self.access_token = None
        self.refresh_token = None
        self.expires_at = 0
        self.user_id = None
        self.user = None

    # -----------------------------
    # PKCE GENERATION
    # -----------------------------
    def _generate_pkce(self):
        self.code_verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b"=").decode()
        code_challenge = hashlib.sha256(self.code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).rstrip(b"=").decode()
        return code_challenge

    # -----------------------------
    # LOGIN URL
    # -----------------------------
    def get_login_url(self):
        code_challenge = self._generate_pkce()
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "scope": self.SCOPES
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    # -----------------------------
    # EXCHANGE CODE FOR TOKEN
    # -----------------------------
    def fetch_token(self, code):
        if not self.code_verifier:
            raise Exception("Missing PKCE code_verifier. Start login first.")

        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code": code,
            "code_verifier": self.code_verifier
        }

        resp = requests.post(self.TOKEN_URL, data=data)
        if resp.status_code != 200:
            raise Exception(f"TIDAL auth error: {resp.status_code} {resp.text}")

        token = resp.json()
        self.access_token = token["access_token"]
        self.refresh_token = token.get("refresh_token")
        self.expires_at = time.time() + token["expires_in"]

        # Get user ID
        user = self.get("/users/me")["data"]
        self.user = TidalUser(user)
        self.user_id = user['id']
        return token

    # -----------------------------
    # REFRESH TOKEN
    # -----------------------------
    def refresh(self):
        if not self.refresh_token:
            raise Exception("No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": self.refresh_token
        }

        resp = requests.post(self.TOKEN_URL, data=data)
        if resp.status_code != 200:
            raise Exception(f"TIDAL refresh error: {resp.status_code} {resp.text}")

        token = resp.json()
        self.access_token = token["access_token"]
        self.expires_at = time.time() + token["expires_in"]
        return token

    # -----------------------------
    # REQUEST WRAPPER
    # -----------------------------
    def _ensure_token(self):
        if not self.access_token or time.time() > self.expires_at:
            self.refresh()

    def _request(self, method, endpoint, params=None, data=None):
        self._ensure_token()
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{self.API_BASE}{endpoint}"
        print("Request url:", url)
        resp = requests.request(method, url, headers=headers, params=params, json=data)
        if resp.status_code not in (200, 201):
            raise Exception(f"TIDAL API error {resp.status_code}: {resp.text}")
        return resp.json()

    def get(self, endpoint, params=None):
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint, data=None):
        return self._request("POST", endpoint, data=data)

    # -----------------------------
    # PLAYLIST METHODS
    # -----------------------------
    def get_user_playlists(self) -> list[TidalPlaylist]:
        params = {
            "filter[owners.id]": self.user_id,
            "countryCode": self.user.country,
            "include": "coverArt,ownerProfiles,items",
            "sort": "-lastModifiedAt"
        }
        playlists = [TidalPlaylist(playlist) for playlist in self.get('/playlists', params=params)["data"]]

        return playlists
        #return self.get(f"/users/{self.user_id}/playlists")

    def fetch_playlistSongs(self, playlist_id) -> list[TidalSong]:
        # : "/playlists/52b1b166-2182-47fd-a04d-f1dffc373361/relationships/items?countryCode=DE&sort=-lastModifiedAt"
        params = {
            'countryCode': self.user.country,
            'sort': '-lastModifiedAt',
            'include': 'items',
        }
        # songs = self.get(f'/playlists/{playlist_id}/relationships/items', params=params)["data"]
        # print(json.dumps(songs, indent=2))
        #songs = [self.fetch_songdata(song['id']) for song in self.get(f'/playlists/{playlist_id}/relationships/items', params=params)["data"]]
        songs = self.fetch_playlist_song_data([song['id'] for song in self.get(f'/playlists/{playlist_id}/relationships/items', params=params)["data"]])
        for song in songs:
            print(f"{song.name} ({song.id})")
        songs = [TidalSong(song) for song in
                 self.get(f'/playlists/{playlist_id}/relationships/items', params=params)["data"]]
        return songs

    def fetch_playlist_song_data(self, songs: list[str]) -> list[TidalSong]:
        params = {
            'filter[id]': [song for song in songs],
            'include': 'coverArt,artists,genres',
            'countryCode': self.user.country
        }
        songs = [TidalSong(data) for data in self.get(f'/tracks', params=params)['data']]
        return songs

    def create_playlist(self, title, description=""):
        payload = {"title": title, "description": description}
        return self.post(f"/users/{self.user_id}/playlists", payload)

    def add_tracks_to_playlist(self, playlist_id, track_ids):
        payload = {"trackIds": track_ids}
        return self.post(f"/playlists/{playlist_id}/items", payload)

    def get_playlist_items(self, playlist_id):
        return self.get(f"/playlists/{playlist_id}/items")

    def get_track(self, track_id):
        return self.get(f"/tracks/{track_id}")

