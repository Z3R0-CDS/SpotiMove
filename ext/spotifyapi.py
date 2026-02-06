import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ext.music_platform import MusicApi, Playlist, Track, Platform


class Spotify_API(MusicApi):
    """Spotify API class"""

    def __init__(self, client_id, client_secret, redirect_uri, scope='user-library-read user-library-modify playlist-modify-public playlist-read-private user-read-private'):
        self.access_token = None
        self.oauth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope
        )
        super().__init__(Platform.SPOTIFY)
 
    def create_spotify_client(self):
        if not self.access_token:
            raise Exception("Access token is not set. Please authenticate first.")
        return spotipy.Spotify(auth=self.access_token['access_token'])
    
    #### ABSTRACT METHODS ####

    def get_login_url(self):
        return self.oauth.get_authorize_url()

    def fetch_token(self, code):
        token = self.oauth.get_access_token(code)
        self.access_token = token
        return token

    def get_user_playlists(self, as_dict=False, with_tracks=False) -> list[Playlist] | list[dict]:
        try:
            sp = self.create_spotify_client()
            playlists = sp.current_user_playlists()['items']
            if with_tracks:
                for playlist in playlists:
                    tracks = sp.playlist_tracks(playlist['id'])['items']
                    if as_dict:
                        playlist['tracks'] = tracks
                    else:
                        playlist['tracks'] = [Track(track=track, platform=self.platform) for track in tracks]
            if as_dict:
                return {"data": [Playlist(playlist, self.platform, with_tracks).to_dict() for playlist in playlists]}
            else:
                return {"data": [Playlist(playlist, self.platform, with_tracks) for playlist in playlists]}
        except Exception as e:
            print(f"Error fetching SPOTIFY playlists: {e}")
            return {"error": "Spotify authentication failed"}
        
    # TODO: Hide local tracks?!

    def find_playlist_by_id(self, id) -> Playlist:
        try:
            sp = self.create_spotify_client()
            playlist = sp.playlist(id)
            return {"data": Playlist(playlist, platform=self.platform)}
        except Exception as e:
            print(f"Error searching playlist: {e}")
            return {"error": "Failed to search for playlist"}

    def find_playlist_by_name(self, name) -> Playlist:
        try:
            sp = self.create_spotify_client()
            playlists = sp.current_user_playlists()['items']
            for playlist in playlists:
                if playlist['name'].lower() == name.lower():
                    tracks = sp.playlist_tracks(playlist['id'])['items']
                    playlist['tracks'] = [Track(track['track'], platform=self.platform) for track in tracks]
                    return {"data": Playlist(playlist, platform=self.platform)}
            return {"error": "Playlist not found"}
        except Exception as e:
            print(f"Error searching playlist: {e}")
            return {"error": "Failed to search for playlist"}
    
    def create_playlist(self, playlist: Playlist)-> Playlist:
        try:
            sp = self.create_spotify_client()
            user_id = sp.current_user()['id']
            playlist = sp.user_playlist_create(user=user_id, name=playlist.name, public=playlist.public, description=playlist.description)
            tracks = sp.playlist_tracks(playlist['id'])['items']
            playlist['tracks'] = [Track(track['track'], platform=self.platform) for track in tracks]
            return {"data": Playlist(playlist, platform=self.platform)}
        except Exception as e:
            print(f"Error creating playlist: {e}")
            return {"error": "Failed to create playlist"}

    def find_track(self, track: Track)-> list[Track]:
        try:
            sp = self.create_spotify_client()
            query = f"track:{track.name} artist:{track.artist.name}"
            results = sp.search(q=query, type='track', limit=5)
            tracks = [Track(track, platform=self.platform) for track in results['tracks']['items']]
            if not tracks:
                return {"error": "No tracks found"}
            return {"data": tracks}
        except Exception as e:
            print(f"Error searching track: {e}")
            return {"error": "Failed to search for track"}
        
    def add_tracks_to_playlist(self, playlist_id, track_uris):
        try:
            sp = self.create_spotify_client()
            sp.playlist_add_items(playlist_id, track_uris)
            return {"data": "Tracks added successfully"}
        except Exception as e:
            print(f"Error adding tracks: {e}")
            return {"error": "Failed to add tracks to playlist"}
        
    def remove_tracks_from_playlist(self, playlist: Playlist, tracks: list[Track]):
        try:
            sp = self.create_spotify_client()
            track_ids = [track.id if track.platform==self.platform else self.find_track[0].id for track in tracks]
            sp.playlist_remove_all_occurrences_of_items(playlist.id, track_ids)
            return {"data": "Tracks removed successfully"}
        except Exception as e:
            print(f"Error removing tracks: {e}")
            return {"error": "Failed to remove tracks from playlist"}