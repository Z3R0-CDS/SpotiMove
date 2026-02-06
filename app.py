import os
import spotipy
from flask import Flask, redirect, request, session, url_for, jsonify, render_template, abort
from flask_socketio import SocketIO, emit, send
from functools import wraps
from ext.config import ConfigHandle
from ext.legacy_tidalapi import TidalDeviceAuth
from ext.tidalapi import TidalAPI
from ext.spotifyapi import Spotify_API


app = Flask(__name__)
config = ConfigHandle()
app.secret_key = os.urandom(24)  # Use a secure secret key in production
socketio = SocketIO(app)

BASE_REDIRECT = 'https://127.0.0.1:5000/callback'

# Spotify Credentials
SPOTIPY_CLIENT_ID = config.get_item('SPOTIFY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = config.get_item('SPOTIFY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = f'{BASE_REDIRECT}/spotify'

# Configure Spotify OAuth
spotify_client = Spotify_API(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI)

# Tidal API & OAuth
TIDAL_CLIENT_ID = config.get_item('TIDAL_CLIENT_ID')
TIDAL_CLIENT_SECRET = config.get_item('TIDAL_CLIENT_SECRET')
# Configure Tidal OAuth
tidal_auth = TidalDeviceAuth(TIDAL_CLIENT_ID)
tidal_oauth = TidalAPI(client_id=TIDAL_CLIENT_ID, redirect_uri=f'{BASE_REDIRECT}/tidal')


def is_authed():
    """Check if both Spotify and Tidal tokens are stored in session."""
    return session.get('spotify_token') is not None and session.get('tidal_token') is not None


@app.before_request
def require_auth():
    """Restrict access to authenticated users only, except for login routes."""
    allowed_paths = ["/", "/login", "/login/spotify", "/callback/spotify", "/login/tidal", "/callback/tidal"]
    if request.path not in allowed_paths and not is_authed():
        return redirect(url_for('login'))

def login_required():
    def decorator(f):
        # Checks if a user is logged in and otherwise redirects
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # TODO: REPLACE THIS HOLDER WITH AUTH
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route('/')
def home():
    return "Welcome! <a href='/login'>Login</a>"


@app.route('/login')
def login():
    if not session.get('spotify_token'):
        return redirect(url_for('login_spotify'))
    if not session.get('tidal_token'):
        return redirect(url_for('login_tidal'))
    return redirect(url_for('startplaylistsync'))


###############
# SPOTIFY API #
###############

@app.route('/login/spotify')
def login_spotify():
    """Redirect user to Spotify login."""
    return redirect(spotify_client.get_login_url())


@app.route('/callback/spotify')
def spotify_callback():
    """Handle Spotify OAuth callback and store access token."""
    code = request.args.get('code')
    token_info = spotify_client.fetch_token(code)
    session['spotify_token'] = token_info
    return redirect(url_for('sync_songs'))

#############
# TIDAL API #
#############

@app.route("/login/tidal")
def login_tidal():
    login_url = tidal_oauth.get_login_url()
    return redirect(login_url)

@app.route("/callback/tidal")
def callback_tidal():
    code = request.args.get("code")
    if not code:
        return "No code returned by Tidal", 400

    token = tidal_oauth.fetch_token(code)
    session["tidal_token"] = token
    return redirect(url_for('sync_songs'))

@app.route('/sync_songs')
def sync_songs():
    """Fetch playlists from Spotify and Tidal."""
    return redirect(url_for('startplaylistsync'))

@app.route('/playlists')
def startplaylistsync():
    # Sync Tidal to Spotify
    return render_template('bootstrap-playlists.html')

@app.route('/get_playlists')
def get_playlists():
    """Fetch playlists from both Spotify and Tidal."""
    spotify_playlists = spotify_client.get_user_playlists(as_dict=True)
    if not spotify_playlists or 'error' in spotify_playlists:
        spotify_playlists = {"error": "Spotify authentication failed"}
    else:
        spotify_playlists = spotify_playlists['data']
    tidal_response = tidal_oauth.get_user_playlists(as_dict=True)
    return jsonify({'spotify_playlists': spotify_playlists, 'tidal_playlists': tidal_response})

# SYNCING

def createPlayList(playlist, client='TIDAL' ):
    # CURRENT WIP FUNCTION
    sp = spotipy.Spotify(auth=session['spotify_token']['access_token'])
    if client == 'TIDAL':
        pass

    elif client == 'SPOTIFY':
        #Tidal search api /searchresults/{query}
        pass

def syncPlaylists(spotify_playlists, tidal_playlists):
    spotify_playlists = spotify_playlists.copy()
    tidal_playlists = tidal_playlists.copy()
    def track_key(track):
        """Generate a unique key for a track based on name and artist."""
        return f"{track.name.lower().strip()}"

    # index tidal playlists by name once
    tidal_by_name = {
        tidal_oauth.find_playlist_by_id(pid).name: tidal_oauth.find_playlist_by_id(pid)
        for pid in tidal_playlists
    }

    for sp_playlist_id in spotify_playlists:
        sp_playlist = spotify_client.find_playlist_by_id(sp_playlist_id)["data"]

        td_playlist = tidal_by_name.get(sp_playlist.name)
        if not td_playlist:
            continue  # playlist doesn't exist on Tidal

        print(f"\n🔄 Syncing playlist: {sp_playlist.name}")

        spotify_tracks = sp_playlist.tracks
        tidal_tracks = td_playlist.tracks

        spotify_map = {track_key(t): t for t in spotify_tracks}
        tidal_map = {track_key(t): t for t in tidal_tracks}

        spotify_keys = set(spotify_map)
        tidal_keys = set(tidal_map)

        spotify_only = spotify_keys - tidal_keys
        tidal_only = tidal_keys - spotify_keys

        # Spotify → Tidal
        for key in spotify_only:
            track = spotify_map[key]
            print(f"[SPOTIFY → TIDAL] {track.name}")
            socketio.emit(
                "progress",
                {"message": f"Syncing {track.name} to Tidal..."},
                namespace="/sync",
            )

        # Tidal → Spotify
        for key in tidal_only:
            track = tidal_map[key]
            print(f"[TIDAL → SPOTIFY] {track.name}")
            socketio.emit(
                "progress",
                {"message": f"Syncing {track.name} to Spotify..."},
                namespace="/sync",
            )
    # for playlist in spotify_playlists:
    #     createPlayList(playlist, "TIDAL")
    # for playlist in tidal_playlists:
    #     createPlayList(playlist, "SPOTIFY")

@app.route('/sync_selected_playlists', methods=['POST'])
def sync_selected_playlists():
    """Sync selected playlists between Spotify and Tidal."""
    data = request.json
    spotify_playlists = data.get('spotify_playlists', [])
    tidal_playlists = data.get('tidal_playlists', [])
    socketio.send("Testing with testo", namespace='/sync')

    syncPlaylists(spotify_playlists, tidal_playlists)

    return jsonify({'message': 'Sync completed'})

@socketio.on('connect', namespace='/sync')
def welcome(data):
    emit('progress', {'message': f'Connected to backend'}, namespace='/sync')


if __name__ == '__main__':
    app.run(debug=config.get_item('server').get('debug', True), host=config.get_item('server').get('host_ip', '0.0.0.0'), ssl_context=("./certs/localhost.pem", "./certs/localhost-key.pem"))
