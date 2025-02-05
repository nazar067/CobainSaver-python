from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from config import SPOTIFY_PUBLIC, SPOTIFY_PRIVATE

def get_spotify_credentials():
    return SPOTIFY_PUBLIC, SPOTIFY_PRIVATE

def get_spotify_client():
    client_id, client_secret = get_spotify_credentials()
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return Spotify(auth_manager=auth_manager)

def extract_track_id(url: str) -> str:
    return url.split("/")[-1].split("?")[0]

def extract_spotify_id(url: str) -> str:
    return url.split("/")[-1].split("?")[0]