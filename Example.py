import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

# ---- STEP 1: SCRAPE ARTISTS FROM INSOMNIAC ----
def get_event_lineup(event_url):
    response = requests.get(event_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find artist names (Modify this selector based on Insomniac's HTML structure)
    artists = [artist.text.strip() for artist in soup.select('.artist-name-selector')]
    
    return artists

# ---- STEP 2: SPOTIFY AUTH ----
SPOTIPY_CLIENT_ID = "your-client-id"
SPOTIPY_CLIENT_SECRET = "your-client-secret"
SPOTIPY_REDIRECT_URI = "http://localhost:8888/callback"

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
    
    for artist in lineup:
        liked_count = liked_songs.get(artist, 0)
        print(f"{artist}: {liked_count} liked song(s)")

# ---- RUN SCRIPT ----
event_url = "https://www.insomniac.com/event/sample-event"  # Change this to the actual event page
compare_artists(event_url)
