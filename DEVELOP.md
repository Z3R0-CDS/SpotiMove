# Inforamtions to gather for developing

## Contributing to SpotiMove
- Fork
- Create feature branches
- Describe the improvement/fix/feature
- KISS & DRY !
- Also keep the changes short as I will check them manually
    - No one likes big commits.

## About

This md tells you what you need when working with tidals and spotifys api.

Also for my demented mind when I no longer understand my code.

## Spotify

- Developed using the python library <a href="https://spotipy.readthedocs.io/en/2.25.0/">spotipy<a/>

### Needed for auth
SPOTIPY_CLIENT_ID -> ID of your app
SPOTIPY_CLIENT_SECRET -> App Secret
SPOTIPY_REDIRECT_URI -> Url to redirect to. Also you need to add that to your app!

### Authentication

    sp_oauth = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope='user-library-read user-library-modify playlist-modify-public playlist-read-private user-read-private'
    )
    
    Then on the callback url you will get the token via session

    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)

- You can find scopes here.  <a href="https://developer.spotify.com/documentation/web-api/concepts/scopes">API SPECS<a/>

After that just let the user open the url sp_oauth.get_authorize_url() I used flasks redirect for that.

## Tidal (WHAT A MESS! Holy)

### First of all the docs and forums
  - <a href="https://developer.tidal.com/apiref?spec=catalogue-v2&ref=get-single-album&at=THIRD_PARTY">API SPECS<a/>
  - <a href="https://developer.tidal.com/">Developer Dashboard<a/> You can find Docs and App dashboard there.

### Authentication...

I found a new Implementation and this segment needs new documentation. But I am exhausted so not rn.

TLDR; TIDAL_CLIENT_ID & TIDAL_CLIENT_SECRET as always. From the above linked Dashboard.

    This code is to create the auth url.

    TIDAL_API_URL = "https://openapi.tidal.com/v2"
    TIDAL_AUTH_URL = "https://login.tidal.com/authorize"
    TIDAL_TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
    TIDAL_CLIENT_ID = <REPLACE WITH UR APP ID>
    TIDAL_CLIENT_SECRET = <REPLACE WITH UR APP SECRET>
    TIDAL_REDIRECT_URI = <REPLACE WITH UR APP CALLBACK URL>

    def generate_pkce():
        """Generate PKCE code_verifier and code_challenge for Tidal OAuth."""
        code_verifier = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode('utf-8').rstrip("=")
        return code_verifier, code_challenge


    code_verifier, code_challenge = generate_pkce()
    session['code_verifier'] = code_verifier  # Store verifier in session

    auth_url = (
        f"{TIDAL_AUTH_URL}?"
        f"response_type=code&client_id={TIDAL_CLIENT_ID}"
        f"&redirect_uri={TIDAL_REDIRECT_URI}"
        f"&code_challenge={code_challenge}&code_challenge_method=S256&scope=playlists.read"
    )

    User needs to open this auth url then. Scopes need to be set as well found in the developer docs

    And like in spotify you need to get back the token wich looks like this

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

    FUN RIGHT? How or where this code is found? Well good luck googeling for a few month!

