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
from ext.music_platform import Playlist, Track, Artist, Platform, MusicApi


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
    description: str = ""

    def __init__(self, data: dict, songs: list[TidalSong]=[]):
        # TIDAL shape
        attributes = data['attributes']
        self.id = data['id']
        self.name = attributes['name']
        self.songs = songs
        self.created_at = attributes['createdAt']
        self.description = attributes.get('description', '')
        self.public = attributes.get('accessType', "PRIVATE") == 'PUBLIC'

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

class TidalAPI(MusicApi):
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

        super().__init__(Platform.TIDAL)

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
    def get_login_url(self) -> str:
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
    def fetch_token(self, code) -> str:
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
    def get_user_playlists(self, as_dict=False, with_tracks=False) -> list[Playlist] | list[dict]:
        params = {
            "filter[owners.id]": self.user_id,
            "countryCode": self.user.country,
            "include": "coverArt,ownerProfiles,items",
            "sort": "-lastModifiedAt",
        }

        playlists: list[Playlist] = []
        cursor = None

        while True:
            if cursor:
                params["page[cursor]"] = cursor
            else:
                params.pop("page[cursor]", None)

            response = self.get("/playlists", params=params)

            # collect playlists
            playlists.extend(
                Playlist(p, platform=self.platform)
                for p in response.get("data", [])
            )

            # read next cursor
            cursor = (
                response
                .get("links", {})
                .get("meta", {})
                .get("nextCursor")
            )

            # last page
            if not cursor:
                break

        # optional: fetch tracks
        if with_tracks:
            for playlist in playlists:
                playlist.tracks = self.fetch_playlistTracks(playlist.id)
        with open("tidal_playlists_response.json", "w") as f:
            json.dump([playlist.to_dict() for playlist in playlists], f, indent=2)
        if as_dict:
            return [playlist.to_dict() for playlist in playlists]

        return playlists


    def fetch_playlistTracks(self, playlist_id) -> list[Track]:
        params = {
            "countryCode": self.user.country,
            "sort": "-lastModifiedAt",
            "include": "items,items.artists",
        }

        response = self.get(
            f"/playlists/{playlist_id}/relationships/items",
            params=params,
        )

        data = response.get("data", [])
        included = response.get("included", [])

        # index included objects by (type, id)
        included_index = {
            (obj["type"], obj["id"]): obj
            for obj in included
        }

        tracks = []

        for item in data:
            track = included_index.get(("tracks", item["id"]))
            if not track:
                continue

            # resolve artists
            artist_names = []
            for artist_ref in track.get("relationships", {}).get("artists", {}).get("data", []):
                artist = included_index.get(("artists", artist_ref["id"]))
                if artist:
                    artist_names.append({'name': artist["attributes"]["name"], 'id': artist_ref['id']})

            track["artistNames"] = artist_names
            tracks.append(Track(track, platform=self.platform))

        return tracks

    def fetch_playlist_track_data(self, tracks: list[str]) -> list[TidalSong]:
        params = {
            'filter[id]': [track for track in tracks],
            'include': 'coverArt,artists,genres',
            'countryCode': self.user.country
        }
        return self.get(f'/tracks', params=params)['data']

    def create_playlist(self, title, description=""):
        payload = {"title": title, "description": description}
        return self.post(f"/users/{self.user_id}/playlists", payload)

    def add_tracks_to_playlist(self, playlist_id, track_ids):
        payload = {"trackIds": track_ids}
        return self.post(f"/playlists/{playlist_id}/items", payload)

    def get_playlist_items(self, playlist_id):
        return self.get(f"/playlists/{playlist_id}/items")
    
    def remove_tracks_from_playlist(self, playlist, tracks):
        return super().remove_tracks_from_playlist(playlist, tracks)

    def get_track(self, track_id):
        return self.get(f"/tracks/{track_id}")

    def find_playlist_by_name(self, name) -> Playlist:
        playlists = self.get_user_playlists()
        for playlist in playlists:
            if playlist.name.lower() == name.lower():
                return playlist
        raise Exception("Playlist not found")
    
    def find_playlist_by_id(self, playlist_id, as_dict=False) -> Playlist:
        playlist_data = self.get(f"/playlists/{playlist_id}")
        tracks = self.fetch_playlistTracks(playlist_id)
        playlist=playlist_data['data']
        playlist['tracks'] = tracks
        if as_dict:
            return Playlist(playlist, platform=self.platform, with_tracks=True).to_dict()
        return Playlist(playlist, platform=self.platform, with_tracks=True)
    
    def find_track(self, track):
        params = {
            'filter[name]': track.name,
            'filter[artistName]': track.artist.name if isinstance(track.artist, Artist) else track.artist,
            'include': 'artists',
            'countryCode': self.user.country
        }
        results = self.get('/tracks', params=params).get('data', [])
        return [Track(result, platform=self.platform) for result in results]