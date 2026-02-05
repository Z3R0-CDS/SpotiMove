import spotipy
from spotipy.oauth2 import SpotifyOAuth


class Spotify_API:
    """Spotify API class"""

    def __init__(self, client_id, client_secret, redirect_uri, scope='user-library-read user-library-modify playlist-modify-public playlist-read-private user-read-private'):
        self.access_token = None
        self.oauth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope
        )

    def get_login_url(self):
        return self.oauth.get_authorize_url()

    def fetch_token(self, code):
        token = self.oauth.get_access_token(code)
        self.access_token = token
        return token
    
    def create_spotify_client(self):
        if not self.access_token:
            raise Exception("Access token is not set. Please authenticate first.")
        return spotipy.Spotify(auth=self.access_token['access_token'])
    
    def get_user_playlists(self):
        try:
            sp = self.create_spotify_client()
            return {"data": sp.current_user_playlists()['items']}
        except Exception as e:
            print(f"Error fetching playlists: {e}")
            return {"error": "Spotify authentication failed"}
    
    def create_playlist(self, name, public=True, description=''):
        try:
            sp = self.create_spotify_client()
            user_id = sp.current_user()['id']
            playlist = sp.user_playlist_create(user=user_id, name=name, public=public, description=description)
            return {"data": playlist}
        except Exception as e:
            print(f"Error creating playlist: {e}")
            return {"error": "Failed to create playlist"}