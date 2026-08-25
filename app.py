import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from urllib.parse import urlencode, quote, unquote
import time, os
import pandas as pd
import streamlit as st

try:
    SPOTIPY_CLIENT_ID = st.secrets["my_secrets"]["client_id"]
    SPOTIPY_CLIENT_SECRET = st.secrets["my_secrets"]["client_secret"]
    SPOTIPY_REDIRECT_URI = st.secrets["my_secrets"]["redirect_uri"]
except KeyError:
    st.write("API key not found.")


# Known Insomniac festival lineup URLs
FESTIVALS = {
    "Beyond Wonderland SoCal": "https://socal.beyondwonderland.com/lineup/",
    "Beyond Wonderland Chicago": "https://chicago.beyondwonderland.com/lineup/",
    "Dreamstate SoCal": "https://socal.dreamstateusa.com/lineup/",
    "Dreamstate SF": "https://sf.dreamstateusa.com/lineup/",
    "EDC Las Vegas": "https://lasvegas.electricdaisycarnival.com/lineup/",
    "EDC Orlando": "https://orlando.electricdaisycarnival.com/lineup/",
    "Escape Halloween": "https://www.escapehalloween.com/lineup/",
    "Nocturnal Wonderland": "https://www.nocturnalwonderland.com/lineup/",
    "Other (enter URL)": None,
}


auth_manager = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-library-read",
    show_dialog=True
)

# Get query parameters
query_params = st.query_params


# Streamlit App
st.title("FestiBesti: Spotify Liked Songs Comparison")


# ---- STEP 1: SCRAPE ARTISTS FROM INSOMNIAC ----
def get_event_lineup(event_url):
    st.write('Getting artists from ' + event_url)
    try:
        response = requests.get(event_url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        st.error("Request timed out trying to reach the festival page. Check the URL and try again.")
        return []
    except requests.exceptions.HTTPError as e:
        st.error(f"Festival page returned an error: {e}")
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach the festival page: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find artist names (selector is specific to Insomniac's HTML structure)
    artists = [artist.text.strip() for artist in soup.select('ul.lineup__list li')]
    artists = list(set(artists))

    if not artists:
        st.warning("No artists found on that page. The URL may be incorrect or the lineup hasn't been announced yet.")

    return artists


# ---- STEP 2: CHECK LIKED SONGS ----
def get_liked_songs(sp, token_info):
    st.write('Getting liked songs from Spotify')

    try:
        total = sp.current_user_saved_tracks(limit=1)['total']
    except SpotifyException as e:
        st.error(f"Spotify API error while fetching liked songs: {e}")
        return {}

    if total == 0:
        st.warning("This Spotify account has no liked songs.")
        return {}

    st.write(f"Total liked songs: {total}")

    # Fetch liked songs — credit all artists on each track, not just the primary
    liked_songs = {}
    limit = 50
    for offset in range(0, total, limit):
        try:
            results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        except SpotifyException as e:
            st.error(f"Spotify API error at offset {offset}: {e}")
            break

        for item in results['items']:
            for artist in item['track']['artists']:
                artist_name = artist['name']
                liked_songs[artist_name] = liked_songs.get(artist_name, 0) + 1

    return liked_songs


# ---- STEP 3: COMPARE EVENT ARTISTS WITH LIKED SONGS ----
def compare_artists(event_url, sp, token_info):
    lineup = get_event_lineup(event_url)
    if not lineup:
        return pd.DataFrame(columns=["Artist", "Liked Songs"])

    liked_songs = get_liked_songs(sp, token_info)

    data = [{"Artist": artist, "Liked Songs": liked_songs.get(artist, 0)} for artist in lineup]

    return pd.DataFrame(data)


is_authenticated = "code" in query_params

if is_authenticated:
    # ---- AUTHENTICATED: restore event_url from the state param Spotify echoed back ----
    event_url = unquote(query_params.get("state", ""))

    code = query_params["code"]
    token_info = auth_manager.get_access_token(code, check_cache=False)

    if token_info:
        access_token = token_info["access_token"]
        sp = spotipy.Spotify(access_token)

        user_info = sp.current_user()
        st.success(f"Authenticated as {user_info['display_name']}!")

        if event_url:
            df = compare_artists(event_url, sp, token_info)
            if not df.empty:
                df = df.sort_values(by="Liked Songs", ascending=False)
                df = df.reset_index(drop=True)
                st.dataframe(df)
            else:
                st.info("No results to display. Check the festival URL or your liked songs.")
        else:
            st.error("No festival URL found. Please go back and select a festival.")

    else:
        st.error("Authentication failed. Please try again.")

else:
    # ---- NOT AUTHENTICATED: show festival selector and login link ----
    selected_festival = st.selectbox("Select a festival", list(FESTIVALS.keys()))

    if FESTIVALS[selected_festival] is None:
        event_url = st.text_input("Enter Insomniac Event URL", placeholder="https://example.com/lineup/")
    else:
        event_url = FESTIVALS[selected_festival]

    # Encode the selected URL into the Spotify auth state param — Spotify echoes it back on redirect
    if event_url:
        auth_url = auth_manager.get_authorize_url(state=quote(event_url, safe=""))
        st.markdown(f"[Click here to log in with Spotify]({auth_url})")
    else:
        st.info("Select or enter a festival URL to continue.")
