import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import pandas as pd
import streamlit as st

import configparser

import streamlit as st

try:
    SPOTIPY_CLIENT_ID = st.secrets["my_secrets"]["client_id"]
    SPOTIPY_CLIENT_SECRET = st.secrets["my_secrets"]["client_secret"]
    SPOTIPY_REDIRECT_URI = st.secrets["my_secrets"]["redirect_uri"]
    #st.write("API key found:", SPOTIPY_CLIENT_ID)
except KeyError:
    st.write("API key not found. Reading config file.")
    # Load config file
    #config = configparser.ConfigParser()
    #config.read("config.ini")
    # ---- STEP 2: SPOTIFY AUTH ----
    #SPOTIPY_CLIENT_ID = config.get("spotify", "client_id")
    #SPOTIPY_CLIENT_SECRET = config.get("spotify", "client_secret")
    #SPOTIPY_REDIRECT_URI = config.get("spotify", "redirect_uri")


event_url = 'https://socal.beyondwonderland.com/lineup/'

# ---- STEP 1: SCRAPE ARTISTS FROM INSOMNIAC ----
def get_event_lineup(event_url):
    print('Before requesting URL')
    response = requests.get(event_url)
    print('after requesting url')
    soup = BeautifulSoup(response.text, 'html.parser')
    print('after soup')
    
    # Find artist names (Modify this selector based on Insomniac's HTML structure)
    artists = [artist.text.strip() for artist in soup.select('ul.lineup__list li')]
    
    return artists



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
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    return df  # Return DataFrame instead of printing
     
# Streamlit App
st.title("FestiBesti: Spotify Liked Songs Comparison")

event_url = st.text_input("Enter Insomniac Event URL", "https://socal.beyondwonderland.com/lineup/")

if st.button("Get Lineup & Liked Songs"):
    df = compare_artists(event_url)
    print('returned df')
    df = df.sort_values(by="Liked Songs", ascending=False)
    st.dataframe(df)  # Displays as an interactive table