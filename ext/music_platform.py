from abc import ABC, abstractmethod
from dataclasses import dataclass, is_dataclass
from enum import Enum
import json

class Platform(Enum):
    SPOTIFY = "spotify"
    TIDAL = "tidal"

@dataclass
class Artist:
    id: str
    name: str
    platform: Platform


class Track:
    id: str
    name: str
    artist: Artist | list[Artist]
    explicit: bool = False
    platform: Platform

    def __init__(self, track: dict, platform: Platform):
        """Initialize Track from TidalSong or Spotify dictionary."""
        if platform == Platform.TIDAL:
            self.id = track['id']
            self.name = track['attributes']['title']
            self.artist = track['artistNames']
            self.explicit = track.get('explicit', False)
            self.platform = Platform.TIDAL

        elif platform == Platform.SPOTIFY:
            track = track['track']
            artist = None
            artist_data = track['artists']
            if isinstance(artist_data, list):
                artist = [Artist(
                    id=artist['id'],
                    name=artist['name'],
                    platform=Platform.SPOTIFY
                ) for artist in artist_data]
            else:
                artist = Artist(
                    id=artist_data['id'],
                    name=artist_data['name'],
                    platform=Platform.SPOTIFY
                )

            self.artist = artist
            self.id = track['id']
            self.name = track['name']
            self.explicit = track.get('explicit', False)
            self.platform = Platform.SPOTIFY

@dataclass
class Playlist:
    id: str
    name: str
    platform: Platform
    tracks: list[Track]
    track_list: bool
    created_at: str = ""
    public: bool = False
    description: str = ""

    def __init__(self, playlist: dict, platform: Platform, with_tracks=False):
        """Initialize Playlist from dict. Spotify(requires 'tracks' item with songs)."""
        
        if platform == Platform.TIDAL:
            self.id = playlist['id']
            self.name = playlist['attributes']['name']
            self.platform = Platform.TIDAL
            self.tracks = playlist.get('tracks', [])
            self.created_at = playlist.get('created_at', "")
            self.public = playlist.get('public', False)
            self.description = playlist.get('description', "")
        elif platform == Platform.SPOTIFY:
            self.id = playlist['id']
            self.name = playlist['name']
            self.platform = Platform.SPOTIFY
            self.tracks = playlist.get('tracks', [])
            self.created_at = playlist.get('created_at', "")
            self.public = playlist.get('public', False)
            self.description = playlist.get('description', "")
            self.track_list = with_tracks

    def to_dict(self):
        def serialize(obj):
            if is_dataclass(obj):
                return {k: serialize(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [serialize(i) for i in obj]
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            elif isinstance(obj, Enum):
                return obj.value
            else:
                return obj

        return serialize(self)


class MusicApi(ABC):
    """Abstract base class for music platform APIs."""

    def __init__(self, platform: Platform):
        self.platform = platform

    @abstractmethod
    def get_login_url(self)-> str:
        """Get the login URL for the music platform."""
        pass

    @abstractmethod
    def fetch_token(self, code: str) -> str:
        """Fetch the access token using the provided authorization code."""
        pass

    @abstractmethod
    def get_user_playlists(selfas_dict=False, with_tracks=False) -> list[Playlist] | list[dict]:
        """Retrieve the user's playlists."""
        pass

    @abstractmethod
    def find_playlist_by_id(self, id: str) -> Playlist:
        """Find a playlist by ID."""
        pass

    @abstractmethod
    def find_playlist_by_name(self, name: str) -> Playlist:
        """Find a playlist by name."""
        pass

    @abstractmethod
    def create_playlist(self, playlist: Playlist) -> Playlist:
        """Create a new playlist."""
        pass

    @abstractmethod
    def find_track(self, track: Track) -> list[Track]:
        """Find a track by name and artist. Returns a list of 5 when no exact match is found."""
        pass

    @abstractmethod
    def add_tracks_to_playlist(self, playlist: Playlist, tracks: list[Track]) -> bool:
        """Add tracks to a playlist."""
        pass

    @abstractmethod
    def remove_tracks_from_playlist(self, playlist: Playlist, tracks: list[Track]) -> bool:
        """Remove tracks from a playlist."""
        pass