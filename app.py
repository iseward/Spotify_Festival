import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
import time, os
import pandas as pd
import streamlit as st

try:
    SPOTIPY_CLIENT_ID = st.secrets["my_secrets"]["client_id"]
    SPOTIPY_CLIENT_SECRET = st.secrets["my_secrets"]["client_secret"]
    SPOTIPY_REDIRECT_URI = st.secrets["my_secrets"]["redirect_uri"]
except KeyError:
    st.write("API key not found.")


auth_manager = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-library-read",
    show_dialog=True
)

# Get authentication URL
auth_url = auth_manager.get_authorize_url()

# Get query parameters
query_params = st.query_params

    
# Streamlit App
st.title("FestiBesti: Spotify Liked Songs Comparison")


# ---- STEP 1: SCRAPE ARTISTS FROM INSOMNIAC ----
def get_event_lineup(event_url):
    st.write('Getting artists from ' + event_url)
    response = requests.get(event_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find artist names (selector is specific to Insomniac's HTML structure)
    artists = [artist.text.strip() for artist in soup.select('ul.lineup__list li')]
    artists = list(set(artists))
    return artists


# ---- STEP 2: CHECK LIKED SONGS ----
def get_liked_songs(sp, token_info):
    st.write('Getting liked songs from Spotify')

    # Fetch liked songs
    liked_songs = {}
    total = sp.current_user_saved_tracks(limit=1)['total']
    st.write(f"Total liked songs: {total}")
    
    limit = 50
    for offset in range(0, total, limit):
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        
        for item in results['items']:
            artist_name = item['track']['artists'][0]['name']
            liked_songs[artist_name] = liked_songs.get(artist_name, 0) + 1
    
    return liked_songs


# ---- STEP 3: COMPARE EVENT ARTISTS WITH LIKED SONGS ----
def compare_artists(event_url, sp, token_info):
    lineup = get_event_lineup(event_url)
    liked_songs = get_liked_songs(sp, token_info)
    
    data = [{"Artist": artist, "Liked Songs": liked_songs.get(artist, 0)} for artist in lineup]
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    return df


event_url = st.text_input(f"Enter Insomniac Event URL", 'https://socal.beyondwonderland.com/lineup/')

is_authenticated = "code" in query_params

# Authenticate user
if is_authenticated:
    code = query_params["code"]
    token_info = auth_manager.get_access_token(code, check_cache=False)

    if token_info:
        access_token = token_info["access_token"]
        sp = spotipy.Spotify(access_token)

        # Display authenticated user
        user_info = sp.current_user()
        st.success(f"Authenticated as {user_info['display_name']}!")
        
        df = compare_artists(event_url, sp, token_info)
        df = df.sort_values(by="Liked Songs", ascending=False)
        df = df.reset_index(drop=True)
        st.dataframe(df)
    
    else:
        st.error("Authentication failed. Please try again.")
else:
    st.markdown(f"[Click here to log in with Spotify]({auth_url})")
