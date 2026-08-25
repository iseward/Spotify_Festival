# FestiBesti – Project Overview

## What This App Does

FestiBesti is a single-page Streamlit app that cross-references a festival artist lineup against the user's Spotify liked songs. The user selects an Insomniac festival from a dropdown, logs in with Spotify OAuth, and gets back a table of lineup artists sorted by how many of their songs the user has liked. All artists on a track are credited, not just the primary artist.

---

## Folder Structure

```
Spotify_Festival/
├── .cache                  # Spotipy OAuth token cache (auto-generated at runtime, gitignored)
├── .git/                   # Git history
├── .gitignore
├── .kiro/
│   └── steering/
│       └── project-overview.md   # This file
├── .streamlit/
│   └── secrets.toml        # Spotify credentials for Streamlit (gitignored)
├── .venv/                  # Local Python virtual environment (gitignored)
├── app.py                  # The entire application — all logic lives here
├── README.md               # One-line project description
└── requirements.txt        # Pinned Python runtime dependencies
```

---

## Code Structure (app.py)

The app is a single flat file with no modules or subfolders. Execution flows top to bottom:

| Section | What it does |
|---|---|
| Imports & credentials | Imports libs; loads Spotify creds from `st.secrets["my_secrets"]` |
| `FESTIVALS` dict | Maps festival display names to their Insomniac lineup URLs |
| OAuth setup | Creates `SpotifyOAuth` manager with `scope="user-library-read"` |
| Auth URL + query params | Generates Spotify login URL; reads callback `?code=` from URL params |
| `get_event_lineup(event_url)` | Scrapes Insomniac event page with requests + BeautifulSoup (`ul.lineup__list li`) |
| `get_liked_songs(sp, token_info)` | Fetches all liked songs paginated (50/page), builds `{artist: count}` dict; credits all artists per track |
| `compare_artists(event_url, sp, token_info)` | Calls both functions, merges into a pandas DataFrame |
| Festival selector UI | `st.selectbox` of known festivals; "Other" option reveals a free-text URL input |
| Auth URL generation | Selected festival URL is URL-encoded into the OAuth `state` param so Spotify echoes it back on redirect |
| Main auth flow | On redirect, festival URL is decoded from `?state=`; login link or results table shown depending on OAuth state |

### Libraries Used

- `streamlit` — UI framework
- `spotipy` + `SpotifyOAuth` — Spotify Web API + OAuth 2.0
- `requests` + `beautifulsoup4` — lineup scraping
- `pandas` — DataFrame for results
- `time`, `os` — standard library, available for future use

### Known Festivals (FESTIVALS dict)

| Display Name | URL |
|---|---|
| Beyond Wonderland SoCal | https://socal.beyondwonderland.com/lineup/ |
| Beyond Wonderland Chicago | https://chicago.beyondwonderland.com/lineup/ |
| EDC Las Vegas | https://lasvegas.electricdaisycarnival.com/lineup/ |
| EDC Orlando | https://orlando.electricdaisycarnival.com/lineup/ |
| Nocturnal Wonderland | https://www.nocturnalwonderland.com/lineup/ |
| Escape Halloween | https://www.escapehalloween.com/lineup/ |
| Other (enter URL) | None — reveals text input |

To add a festival, add an entry to the `FESTIVALS` dict at the top of `app.py`.

---

## Running the App

```powershell
# Activate venv
.venv\Scripts\activate

# Run locally
streamlit run app.py
```

Spotify redirects to `http://127.0.0.1:8501/` after login. Make sure this URI (and `https://FestiBestiApp.streamlit.app` for deployment) are both registered in the Spotify Developer Dashboard.

---

## Credentials & Auth

- Spotify credentials live in `.streamlit/secrets.toml` under `[my_secrets]` — this file is gitignored.
- `localhost` is **not** allowed as a Spotify redirect URI. Use `http://127.0.0.1:8501/` for local dev.
- Token caching is currently disabled (`check_cache=False`, `show_dialog=True`). This means the user must re-authenticate on every page load. See "Known Limitations" below.

---

## Known Limitations & Remaining Improvements

### 1. Festival selection resets after OAuth redirect (resolved)

The selected festival URL is encoded into the Spotify OAuth `state` parameter, which Spotify echoes back unchanged in the redirect URL (`?code=...&state=<encoded_url>`). The app decodes it on redirect — no session state or tab dependency.

### 2. Token caching / re-auth friction

`show_dialog=True` and `check_cache=False` force a full Spotify login on every page load. To fix, enable caching in `SpotifyOAuth`:

```python
auth_manager = SpotifyOAuth(
    ...
    cache_path=".cache",
    show_dialog=False,
)
```

And remove `check_cache=False` from `get_access_token`. This would also resolve the festival selection reset issue above.

### 3. No error handling

The scraper and Spotify API calls have no try/except. A bad URL, network failure, or expired token will crash the app with a raw Python traceback. Wrap key calls in try/except and surface `st.error(...)` messages.

### 4. Hardcoded Insomniac CSS selector

`get_event_lineup` uses `ul.lineup__list li` — specific to Insomniac's site structure. Non-Insomniac URLs entered via "Other" will return 0 artists silently.

### 5. Only local dev redirect URI in secrets.toml

When deploying to Streamlit Cloud, `redirect_uri` in `secrets.toml` must be changed to `https://FestiBestiApp.streamlit.app`. Consider managing this with separate local vs. deployed secrets rather than manually swapping.
