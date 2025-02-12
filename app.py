from flask import Flask, redirect, request, session, url_for, jsonify, render_template
import requests
import os
import base64
import hashlib
import random
import string

from ext.config import ConfigHandle
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from flask_socketio import SocketIO, emit, send

app = Flask(__name__)
config = ConfigHandle()
app.secret_key = os.urandom(24)  # Use a secure secret key in production
socketio = SocketIO(app)

# Spotify Credentials
SPOTIPY_CLIENT_ID = config.get_item('SPOTIFY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = config.get_item('SPOTIFY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = 'http://localhost:5000/callback/spotify'

# Configure Spotify OAuth
sp_oauth = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope='user-library-read user-library-modify playlist-modify-public playlist-read-private user-read-private'
)

# Tidal API & OAuth
api_v2_location = "https://api.tidal.com/v2"
TIDAL_API_URL = "https://openapi.tidal.com/v2"
TIDAL_AUTH_URL = "https://login.tidal.com/authorize"
TIDAL_TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
TIDAL_CLIENT_ID = config.get_item('TIDAL_CLIENT_ID')
TIDAL_CLIENT_SECRET = config.get_item('TIDAL_CLIENT_SECRET')
TIDAL_REDIRECT_URI = 'http://localhost:5000/callback/tidal'
TIDAL_SCOPE = 'playlists.read playlists.write user.read'


def generate_pkce():
    """Generate PKCE code_verifier and code_challenge for Tidal OAuth."""
    code_verifier = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode('utf-8').rstrip("=")
    return code_verifier, code_challenge


def is_authed():
    """Check if both Spotify and Tidal tokens are stored in session."""
    return session.get('spotify_token') is not None and session.get('tidal_token') is not None


@app.before_request
def require_auth():
    """Restrict access to authenticated users only, except for login routes."""
    allowed_paths = ["/", "/login", "/login/spotify", "/callback/spotify", "/login/tidal", "/callback/tidal"]
    if request.path not in allowed_paths and not is_authed():
        return redirect(url_for('login'))


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


@app.route('/login/spotify')
def login_spotify():
    """Redirect user to Spotify login."""
    return redirect(sp_oauth.get_authorize_url())


@app.route('/callback/spotify')
def spotify_callback():
    """Handle Spotify OAuth callback and store access token."""
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['spotify_token'] = token_info
    return redirect(url_for('sync_songs'))


@app.route('/login/tidal')
def login_tidal():
    """Redirect user to Tidal login with PKCE."""
    code_verifier, code_challenge = generate_pkce()
    session['code_verifier'] = code_verifier  # Store verifier in session

    auth_url = (
        f"{TIDAL_AUTH_URL}?"
        f"response_type=code&client_id={TIDAL_CLIENT_ID}"
        f"&redirect_uri={TIDAL_REDIRECT_URI}"
        f"&code_challenge={code_challenge}&code_challenge_method=S256&scope={TIDAL_SCOPE}"
    )
    return redirect(auth_url)


@app.route('/callback/tidal')
def tidal_callback():
    """Handle Tidal OAuth callback and get access token."""
    code = request.args.get("code")
    if not code:
        return "No code provided!", 400

    code_verifier = session.pop('code_verifier', None)
    if not code_verifier:
        return "Missing PKCE verifier!", 400

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": TIDAL_REDIRECT_URI,
        "client_id": TIDAL_CLIENT_ID,
        "client_secret": TIDAL_CLIENT_SECRET,
        "code_verifier": code_verifier
    }

    response = requests.post(TIDAL_TOKEN_URL, data=token_data)
    if response.status_code == 200:
        session["tidal_token"] = response.json()
        return redirect(url_for('sync_songs'))
    return f"Failed to get token: {response.text}", response.status_code


@app.route('/sync_songs')
def sync_songs():
    """Fetch playlists from Spotify and Tidal."""
    return redirect(url_for('startplaylistsync'))

@app.route('/playlists')
def startplaylistsync():
    # Sync Tidal to Spotify
    return render_template('bootstrap-playlists.html')

def get_spotify_playlists():
    """Retrieve the user's Spotify playlists."""
    sp = spotipy.Spotify(auth=session['spotify_token']['access_token'])
    return sp.current_user_playlists()['items']


def get_tidal_playlists():
    """Retrieve the user's Tidal playlists."""
    access_token = session.get("tidal_token", {}).get("access_token")
    if not access_token:
        return {"error": "Not logged into Tidal"}, 401

    headers = {"Authorization": f"Bearer {access_token}"}
    playlists_url = f"{TIDAL_API_URL}/playlists/me"

    #playlists_url = "https://listen.tidal.com/v2/my-collection/playlists/folders?folderId=root"

    response = requests.get(playlists_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}, response.status_code


@app.route('/get_playlists')
def get_playlists():
    """Fetch playlists from both Spotify and Tidal."""
    try:
        spotify_playlists = [{'name': p['name'], 'id': p['id']} for p in get_spotify_playlists()]
    except:
        spotify_playlists = {"error": "Spotify authentication failed"}

    tidal_response = get_tidal_playlists()
    if isinstance(tidal_response, tuple):
        tidal_playlists = {"error": tidal_response[1]}
    else:
        tidal_playlists = [{'name': p['attributes']['name'], 'id': p['id']} for p in tidal_response.get("data", [])]

    return jsonify({'spotify_playlists': spotify_playlists, 'tidal_playlists': tidal_playlists})

# SYNCING

def createPlayList(playlist, client='TIDAL' ):
    # CURRENT WIP FUNCTION
    sp = spotipy.Spotify(auth=session['spotify_token']['access_token'])
    print(playlist)
    if client == 'TIDAL':
        playlist = sp.playlist(playlist)
        print(playlist)
        songs = sp.playlist_items(playlist['id'])
        #my-collection/playlists/folders/create-playlist
        #https://listen.tidal.com/v2/suggestions/?countryCode=DE&locale=en_US&deviceType=BROWSER&explicit=true&hybrid=true&query=test12

        access_token = session.get("tidal_token", {}).get("access_token")
        if not access_token:
            return {"error": "Not logged into Tidal"}, 401
        headers = {"Authorization": f"Bearer {access_token}"}
        playlists_url = f"{api_v2_location}/my-collection/playlists/folders/create-playlist"
        # playlists_url = "https://listen.tidal.com/v2/my-collection/playlists/folders?folderId=root"
        params = {"name": playlist['name'], "description": "None", "folderId": "root"}
        response = requests.get(playlists_url, headers=headers, params=params)
        if response.status_code == 200:
            print(response.json())
            return response.json()
        else:
            print(f"Failed to create playlist:({response.status_code}) {response.text} ")
            return {"error": response.json()}, response.status_code


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
    app.run(debug=True)
