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
    spotify_playlists = spotify_client.get_user_playlists()
    if not spotify_playlists or 'error' in spotify_playlists:
        spotify_playlists = {"error": "Spotify authentication failed"}
    else:
        spotify_playlists = [{'name': p['name'], 'id': p['id']} for p in spotify_client.get_user_playlists()['data']]
    tidal_response = tidal_oauth.get_user_playlists(as_dict=True)
    return jsonify({'spotify_playlists': spotify_playlists, 'tidal_playlists': tidal_response})

# SYNCING

def createPlayList(playlist, client='TIDAL' ):
    # CURRENT WIP FUNCTION
    sp = spotipy.Spotify(auth=session['spotify_token']['access_token'])
    print(playlist)
    if client == 'TIDAL':
        pass

    elif client == 'SPOTIFY':
        #Tidal search api /searchresults/{query}
        pass

@app.route('/sync_selected_playlists', methods=['POST'])
def sync_selected_playlists():
    """Sync selected playlists between Spotify and Tidal."""
    data = request.json
    spotify_playlists = data.get('spotify_playlists', [])
    tidal_playlists = data.get('tidal_playlists', [])
    socketio.send("Testing with testo", namespace='/sync')

    for playlist in spotify_playlists:
        socketio.emit('progress', {'message': f'Syncing {playlist} to Tidal...'}, namespace='/sync')
        for tdplaylist in tidal_playlists:
            if tdplaylist['name'] == playlist['name']:
                # TODO append missing songs
                pass
        createPlayList(playlist, "TIDAL")

        # Implement sync logic here

    for playlist in tidal_playlists:
        socketio.emit('progress', {'message': f'Syncing {playlist} to Spotify...'}, namespace='/sync')
        # Implement sync logic here

    return jsonify({'message': 'Sync completed'})

@socketio.on('connect', namespace='/sync')
def welcome(data):
    emit('progress', {'message': f'Connected to backend'}, namespace='/sync')


if __name__ == '__main__':
    app.run(debug=config.get_item('server').get('debug', True), host=config.get_item('server').get('host_ip', '0.0.0.0'), ssl_context=("./certs/localhost.pem", "./certs/localhost-key.pem"))
