# SpotiMove
Status: Under development

## About
    Hey there fella. 
    This project is an open source spotify & tidal syncer (someone could add more)
    I aim to make it easy to sync playlists between those apps without any pay(ofc if you aim to selfhost).
    All easy and in one place with OAuth.
    PLEASE help me with merge requests or information to improve this project and or fix current issues.

## Release

There will be a release when I have a working version ready. <br>
The plan is a single executable wich can be used for localhost and a online version behind a future domain.

## Status
    Currently in "early" development took a while to get here but I work on and off on it
    Does need some help and love!

## Disclaimer
    Even when I release the app I DO NOT gurantee any support or long term development.
    The app is made for personal use but can help others so I publish it.
    It might contain automation wich is not allowed in TOS esp when used for a business. Keep that in mind.
    It is not intendet for company use but rather private.

## Issues
- Implementations for syncs are neither tested nor really developed. So that is the next step

More on issues tab
    

## Want haves
- Playlist images as icon

## TODO
- Overall
  - [x] Improve to ui (bit... well ugly)
  - [ ] Remove legacy Tidal connection
  - [x] Move Spotify interactions to separate class?
- Spotify
  - [x] Get OAuth login
  - [x] Get Playlists
  - [x] Get Tracks from playlists
  - [ ] Create Playlist
  - [ ] Search for Songs via name and artist
- TIDAL
  - [x] Get OAuth login (NIGHTMARE!)
  - [x] Get Playlists
  - [x] Get Tracks from playlists
  - [ ] Create Playlist
    - User.read perms needed for the endpoint I found (switched api and can use user.read atm... Cannot find old api docs)
      - Rate limits or denies OAuth
  - [ ] Search for Songs via name and artist

## 3rd party projects used
- THANK GOD no OAuth implementation needed for spotify thanks to <a href="https://spotipy.readthedocs.io/en/2.25.0/">spotipy</a>
- Basics: Flask & flask-socketio
- Frontend: socketio & bootstrap.min
- <a href="https://github.com/spotify2tidal/spotify_to_tidal">Spotify to TIDAL</a> also helped a lot along the way. But imo cli is not enough or the way
- And ofc my own Zero Industries code libary parts. Wich are not public yet so I will commit used parts for now.