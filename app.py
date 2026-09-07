import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from urllib.parse import quote, unquote
import time, os
import pandas as pd
import streamlit as st

try:
    SPOTIPY_CLIENT_ID = st.secrets["my_secrets"]["client_id"]
    SPOTIPY_CLIENT_SECRET = st.secrets["my_secrets"]["client_secret"]
    SPOTIPY_REDIRECT_URI = st.secrets["my_secrets"]["redirect_uri"]
except KeyError:
    st.error("Spotify API credentials not found. Check your secrets.toml configuration.")
    st.stop()


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

class _NoCache(spotipy.cache_handler.CacheHandler):
    """No-op cache handler — prevents Spotipy from reading or writing any token cache file."""
    def get_cached_token(self):
        return None
    def save_token_to_cache(self, token_info):
        pass

auth_manager = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-library-read",
    show_dialog=False,
    cache_handler=_NoCache(),   # Tokens live in session_state only — no disk writes
)

query_params = st.query_params

st.title("FestiBesti: Spotify Liked Songs Comparison")


# ---- HELPERS ----

def get_valid_token():
    """Return a valid access token from session state, refreshing if expired. Returns None if not authenticated."""
    token_info = st.session_state.get("token_info")
    if not token_info:
        return None
    if auth_manager.is_token_expired(token_info):
        try:
            token_info = auth_manager.refresh_access_token(token_info["refresh_token"])
            st.session_state["token_info"] = token_info
        except Exception:
            # Refresh failed — clear session and force re-auth
            st.session_state.pop("token_info", None)
            return None
    return token_info


def get_event_lineup(event_url):
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

    # Selector is specific to Insomniac's HTML structure
    artists = [artist.text.strip() for artist in soup.select('ul.lineup__list li')]
    artists = list(set(artists))

    if not artists:
        st.warning("No artists found on that page. The URL may be incorrect or the lineup hasn't been announced yet.")

    return artists


def get_liked_songs(sp):
    try:
        total = sp.current_user_saved_tracks(limit=1)['total']
    except SpotifyException as e:
        st.error(f"Spotify API error while fetching liked songs: {e}")
        return {}

    if total == 0:
        st.warning("This Spotify account has no liked songs. Make sure you're logged into the right account.")
        return {}

    st.write(f"Total liked songs: {total}")

    # Credit all artists on each track, not just the primary
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


def compare_artists(event_url, sp):
    lineup = get_event_lineup(event_url)
    if not lineup:
        return pd.DataFrame(columns=["Artist", "Liked Songs"])

    liked_songs = get_liked_songs(sp)
    data = [{"Artist": artist, "Liked Songs": liked_songs.get(artist, 0)} for artist in lineup]
    return pd.DataFrame(data)


def do_logout():
    st.session_state.pop("token_info", None)
    st.session_state.pop("event_url", None)
    st.session_state["show_dialog"] = True
    st.query_params.clear()


# ---- AUTH FLOW ----

# Step 1: OAuth callback — exchange code for token and store in session state
if "code" in query_params and "token_info" not in st.session_state:
    code = query_params["code"]
    event_url_from_state = unquote(query_params.get("state", ""))
    try:
        token_info = auth_manager.get_access_token(code)
        st.session_state["token_info"] = token_info
        if event_url_from_state:
            st.session_state["event_url"] = event_url_from_state
    except Exception as e:
        st.error(f"Authentication failed: {e}")
    # Clear query params so ?code= doesn't persist on reruns
    st.query_params.clear()
    st.rerun()

# Step 2: Check for a valid token in session state
token_info = get_valid_token()

# ---- AUTHENTICATED VIEW ----
if token_info:
    sp = spotipy.Spotify(auth=token_info["access_token"])

    try:
        user_info = sp.current_user()
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"Authenticated as {user_info['display_name']}")
        with col2:
            if st.button("Log out"):
                do_logout()
                st.rerun()
    except SpotifyException:
        st.error("Could not retrieve Spotify user info. Please log in again.")
        do_logout()
        st.rerun()

    # Festival selector — pre-select based on session state if coming from OAuth redirect
    festival_names = list(FESTIVALS.keys())
    stored_url = st.session_state.get("event_url", "")
    # Find which festival name matches the stored URL, fall back to first entry
    url_to_name = {v: k for k, v in FESTIVALS.items() if v is not None}
    default_festival = url_to_name.get(stored_url, festival_names[0])
    default_index = festival_names.index(default_festival)

    selected_festival = st.selectbox("Select a festival", festival_names, index=default_index)
    if FESTIVALS[selected_festival] is None:
        event_url = st.text_input("Enter Insomniac Event URL", placeholder="https://example.com/lineup/", value=stored_url)
    else:
        event_url = FESTIVALS[selected_festival]

    if st.button("Compare"):
        if event_url:
            with st.spinner("Fetching lineup and liked songs..."):
                df = compare_artists(event_url, sp)
            if not df.empty:
                df = df.sort_values(by="Liked Songs", ascending=False)
                df = df.reset_index(drop=True)
                st.dataframe(df)
            else:
                st.info("No results to display. Check the festival URL or your liked songs.")
        else:
            st.warning("Please select or enter a festival URL.")

# ---- UNAUTHENTICATED VIEW ----
else:
    selected_festival = st.selectbox("Select a festival", list(FESTIVALS.keys()))
    if FESTIVALS[selected_festival] is None:
        event_url = st.text_input("Enter Insomniac Event URL", placeholder="https://example.com/lineup/")
    else:
        event_url = FESTIVALS[selected_festival]

    if event_url:
        show_dialog = st.session_state.pop("show_dialog", False)
        auth_url = auth_manager.get_authorize_url(state=quote(event_url, safe=""))
        # If coming from a logout, force Spotify to show the account picker
        if show_dialog:
            auth_url += "&show_dialog=true"
        st.markdown(f"[Click here to log in with Spotify]({auth_url})")
    else:
        st.info("Select or enter a festival URL to continue.")
