import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import pandas as pd

import configparser

# Load config file
config = configparser.ConfigParser()
config.read("config.ini")

event_url = 'https://socal.beyondwonderland.com/lineup/'

# ---- STEP 1: SCRAPE ARTISTS FROM INSOMNIAC ----
def get_event_lineup(event_url):
    response = requests.get(event_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find artist names (Modify this selector based on Insomniac's HTML structure)
    artists = [artist.text.strip() for artist in soup.select('ul.lineup__list li')]
    
    return artists

# ---- STEP 2: SPOTIFY AUTH ----
SPOTIPY_CLIENT_ID = config.get("spotify", "client_id")
SPOTIPY_CLIENT_SECRET = config.get("spotify", "client_secret")
SPOTIPY_REDIRECT_URI = config.get("spotify", "redirect_uri")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-library-read"
))

# ---- STEP 3: CHECK LIKED SONGS ----
def get_liked_songs():
    liked_songs = {}
    results = sp.current_user_saved_tracks(limit=50)
    
    while results:
        for item in results['items']:
            artist_name = item['track']['artists'][0]['name']
            liked_songs[artist_name] = liked_songs.get(artist_name, 0) + 1
        
        results = sp.next(results) if results['next'] else None
    
    return liked_songs

# ---- STEP 4: COMPARE EVENT ARTISTS WITH LIKED SONGS ----
def compare_artists(event_url):
    lineup = get_event_lineup(event_url)
    liked_songs = get_liked_songs()
    
    data = [{"Artist": artist, "Liked Songs": liked_songs.get(artist, 0)} for artist in lineup]
    
    #for artist in lineup:
    #    liked_count = liked_songs.get(artist, 0)
    #    # Create a list of dictionaries
    #     print(f"{artist}: {liked_count} liked song(s)")
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    return df  # Return DataFrame instead of printing
     
# ---- RUN SCRIPT ----
df = compare_artists(event_url)
# Sort by Liked Songs in descending order
df = df.sort_values(by="Liked Songs", ascending=False)