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


# Set up Spotify authentication
auth_manager = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-library-read",
    show_dialog=True,
    cache_path=".spotify_cache"  # Caching helps with re-authentication
)

# Get authentication URL
auth_url = auth_manager.get_authorize_url()

# Get query parameters
query_params = st.query_params




# Authenticate user
if "code" in query_params:
    code = query_params["code"]
    token_info = auth_manager.get_access_token(code)
    st.write(token_info)
    
    if token_info:
        access_token = token_info["access_token"]
        sp = spotipy.Spotify(auth=access_token)

        # Display authenticated user
        user_info = sp.current_user()
        st.success(f"Authenticated as {user_info['display_name']}!")

        # Save token in session state for reuse
        st.session_state["token_info"] = token_info
    else:
        st.error("Authentication failed. Please try again.")

# If user has already logged in before, use cached token
elif "token_info" in st.session_state:
    token_info = auth_manager.get_cached_token()
    print(f"token_info: ", token_info)
    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])



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
def get_liked_songs():
    st.write('Getting liked songs from Spotify')
    liked_songs = {}
    total = sp.current_user_saved_tracks(limit=1)['total']  # Get total liked songs
    #st.write(f"Total liked songs: {total}")
    
    limit = 50
    for offset in range(0, total, limit):  # Iterate through all pages
        #st.write(f"Getting liked songs in batch: {offset}")
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        
        for item in results['items']:
            artist_name = item['track']['artists'][0]['name']
            liked_songs[artist_name] = liked_songs.get(artist_name, 0) + 1
    
    return liked_songs


# ---- STEP 4: COMPARE EVENT ARTISTS WITH LIKED SONGS ----
def compare_artists(event_url):
    lineup = get_event_lineup(event_url)
    #st.write('Getting liked songs')
    liked_songs = get_liked_songs()
    
    data = [{"Artist": artist, "Liked Songs": liked_songs.get(artist, 0)} for artist in lineup]
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    return df  # Return DataFrame instead of printing


     
# Streamlit App
st.title("FestiBesti: Spotify Liked Songs Comparison")

event_url = st.text_input("Enter Insomniac Event URL", "https://socal.beyondwonderland.com/lineup/")


# Check if user is authenticated
is_authenticated = "token_info" in st.session_state

# Show login button if user is not authenticated
if not is_authenticated:
    st.markdown(f"[Click here to log in with Spotify]({auth_url})")

# Disable the button if the user is not authenticated
button_disabled = not is_authenticated
button_label = "Get Lineup & Liked Songs" if is_authenticated else "Log in to Spotify to see results"


# Create the button (disabled if not authenticated)
if st.button(button_label, disabled=button_disabled):
    #st.write('after auth check')
    df = compare_artists(event_url)
    df = df.sort_values(by="Liked Songs", ascending=False)
    # Reset index
    df = df.reset_index(drop=True)
    st.dataframe(df)  # Displays as an interactive table