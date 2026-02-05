# SpotiMove
WIP & requires support prob
(most things are patched but software not fully developed or tested yet. Check tidal-patch branch)

## About
    Hey there fella. 
    This project is an open source spotify & tidal syncer
    I aim to make it easy to sync playlists between those apps without any pay.
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
    Also it is under the licence 

## Issues
- [ ] Currently tidal blocks perm requests for user.read for some reason and blocks the ip
  - Add function to check the X-RateLimit-Remaining for rate limit issue
  - Somehow get all 3 perms under 1 roof
    

## TODO
- Spotify
  - [x] Get OAuth login
  - [x] Get Playlists
  - [x] Get Tracks from playlists
  - [ ] Create Playlist
  - [ ] Search for Songs via name and artist
- TIDAL
  - [x] Get OAuth login (NIGHTMARE)
  - [x] Get Playlists
  - [x] Get Tracks from playlists
  - [ ] Create Playlist
    - User.read perms needed for the endpoint I found
      - Rate limits or denies OAuth
  - [ ] Search for Songs via name and artist

## 3rd party projects used
- THANK GOD no OAuth implementation needed for spotify thanks to <a href="https://spotipy.readthedocs.io/en/2.25.0/">spotipy<a/>
- Basics: Flask & flask-socketio
- Frontend: socketio & bootstrap.min
- And ofc my own Zero Industries code libary parts. Wich are not public yet so I will commit used parts for now.
