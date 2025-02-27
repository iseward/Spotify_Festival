import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
import time, os
import pandas as pd
import streamlit as st
import configparser

try:
    SPOTIPY_CLIENT_ID = st.secrets["my_secrets"]["client_id"]
    SPOTIPY_CLIENT_SECRET = st.secrets["my_secrets"]["client_secret"]
    SPOTIPY_REDIRECT_URI = st.secrets["my_secrets"]["redirect_uri"]
except KeyError:
    st.write("API key not found.")


event_url = 'https://socal.beyondwonderland.com/lineup/'


auth_manager = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-library-read",          #user-read-private
    show_dialog=True
    #,    cache_path=".cache"
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
    #st.write('after requesting url')
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find artist names (Modify this selector based on Insomniac's HTML structure)
    artists = [artist.text.strip() for artist in soup.select('ul.lineup__list li')]
    artists = list(set(artists))
    #st.write('Getting artists from ' + event_url)
    return artists


# ---- STEP 3: CHECK LIKED SONGS ----
def get_liked_songs(sp):
    st.write('Getting liked songs from Spotify')
    print(f"Getting songs with token: ", token_info)

    # Fetch liked songs
    liked_songs = {}
    total = sp.current_user_saved_tracks(limit=1)['total']  # Get total liked songs
    st.write(f"Total liked songs: {total}")
    
    limit = 50
    for offset in range(0, total, limit):
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        
        for item in results['items']:
            artist_name = item['track']['artists'][0]['name']
            liked_songs[artist_name] = liked_songs.get(artist_name, 0) + 1
    
    return liked_songs


# ---- STEP 4: COMPARE EVENT ARTISTS WITH LIKED SONGS ----
def compare_artists(event_url, sp):
    lineup = get_event_lineup(event_url)
    #st.write('Getting liked songs')
    liked_songs = get_liked_songs(sp)
    
    data = [{"Artist": artist, "Liked Songs": liked_songs.get(artist, 0)} for artist in lineup]
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    return df  # Return DataFrame instead of printing


event_url = st.text_input(f"Enter Insomniac Event URL", event_url)

is_authenticated = "code" in query_params

# Authenticate user
if is_authenticated:
    code = query_params["code"]
    #print(f"Code: ", code)
    #st.write(f"Code: ", code)
    #token_info = auth_manager.get_access_token(code)  # This does not work due to caching issues
    token_info = auth_manager.get_access_token(code, check_cache=False)  # 
    #token_info = auth_manager.get_access_token(code, as_dict=True, check_cache=False)  # Ensure full token dict
    print(f"token_info: ", token_info)

    if token_info:
        access_token = token_info["access_token"]  # Extract actual access token
        sp = spotipy.Spotify(access_token)

        # Display authenticated user
        user_info = sp.current_user()
        st.success(f"Authenticated as {user_info['display_name']}!")  # This should now show the correct user
        #st.write(f"Token expired? ", auth_manager.is_token_expired(token_info))
        
        df = compare_artists(event_url, sp)
        df = df.sort_values(by="Liked Songs", ascending=False)
        # Reset index
        df = df.reset_index(drop=True)
        st.dataframe(df)  # Displays as an interactive table
    
    else:
        st.error("Authentication failed. Please try again.")
else:
    st.markdown(f"[Click here to log in with Spotify]({auth_url})")




