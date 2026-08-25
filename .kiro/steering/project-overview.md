# FestiBesti – Project Overview

## What This App Does

FestiBesti is a single-page Streamlit app that cross-references a festival artist lineup against the user's Spotify liked songs. The user pastes an Insomniac event URL, logs in with Spotify OAuth, and gets back a table of lineup artists sorted by how many of their songs the user has liked.

---

## Folder Structure

```
Spotify_Festival/
├── .cache                  # Spotipy OAuth token cache (auto-generated at runtime)
├── .git/                   # Git history
├── .gitignore
├── .kiro/
│   └── steering/
│       └── project-overview.md   # This file
├── .streamlit/
│   └── secrets.toml        # Spotify credentials for Streamlit (gitignored)
├── app.py                  # The entire application — all logic lives here
├── config.ini              # Legacy credential file (gitignored, no longer read by the app)
├── README.md               # One-line project description
└── requirements.txt        # Python runtime dependencies
```

---

## Code Structure (app.py)

The app is a single flat file with no modules or subfolders. Execution flows top to bottom:

| Section | Lines (approx.) | What it does |
|---|---|---|
| Imports & credentials | 1–17 | Imports libs; loads Spotify creds from `st.secrets["my_secrets"]` |
| OAuth setup | 20–30 | Creates `SpotifyOAuth` manager with `scope="user-library-read"` |
| Auth URL + query params | 32–36 | Generates Spotify login URL; reads callback `?code=` from URL params |
| Page title | 39 | `st.title(...)` |
| `get_event_lineup(event_url)` | 42–51 | Scrapes Insomniac event page with requests + BeautifulSoup (`ul.lineup__list li`) |
| `get_liked_songs(sp)` | 54–68 | Fetches all liked songs paginated (50/page), builds `{artist: count}` dict |
| `compare_artists(event_url, sp)` | 71–82 | Calls both functions, merges into a pandas DataFrame |
| Main UI flow | 84–113 | Text input for URL, login link or authenticated table depending on OAuth state |

### Libraries Used

- `streamlit` — UI framework
- `spotipy` + `SpotifyOAuth` — Spotify Web API + OAuth 2.0
- `requests` + `beautifulsoup4` — lineup scraping
- `pandas` — DataFrame for results
- `configparser` — **imported but never used** (dead code, legacy of `config.ini` era)

---

## Known Issues & Improvement Tips

### 1. Pin dependency versions in requirements.txt

Currently all four deps are unpinned (e.g. `streamlit`, `spotipy`). This means `pip install` can pull breaking versions. Pin them:

```
beautifulsoup4==4.12.3
spotipy==2.24.0
streamlit==1.37.0
pandas==2.2.2
```

Run `pip freeze > requirements.txt` (inside `.venv`) to capture exact versions.

Also, `requests` is used in the code but missing from `requirements.txt`. It works today as a transitive dep but should be explicit.

### 2. Use a .venv for isolation

There's no `.venv` in the repo. Add one:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Add `.venv/` to `.gitignore` (it's not there yet).

### 3. Fix .gitignore — .cache is not excluded

`.gitignore` excludes `.spotify_cache` but the actual Spotipy token cache is named `.cache`. That file could end up committed. Add `.cache` to `.gitignore`.

### 4. Remove dead code

- `import configparser` is never used — remove it.
- The `config.ini` file is no longer read by the app. Delete it or leave it as a local-only reference, but the import should go.
- `event_url` is assigned at the top of `app.py` but the `st.text_input` default overrides it — the first assignment is redundant.

### 5. Token caching / re-auth friction

`cache_path` is commented out in `SpotifyOAuth` and `check_cache=False` is passed to `get_access_token`. Combined with `show_dialog=True`, the user is forced to re-authenticate on every page load. Enable caching to improve UX:

```python
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="user-library-read",
    cache_path=".cache",
    show_dialog=False,
)
```

### 6. Add error handling

The scraper and Spotify calls have no try/except. If the event URL is wrong or the network is down, the app crashes. Wrap the main logic in try/except and surface a friendly `st.error(...)` message.

### 7. Multi-artist tracks only credit artist[0]

`get_liked_songs` only counts `artists[0]` per track. A song with two artists only increments the first. This could undercount headliners who appear in collabs.

### 8. Credential management

- `config.ini` has plaintext Spotify credentials. It's gitignored, but the app has fully migrated to `.streamlit/secrets.toml` — `config.ini` can be deleted.
- The redirect URI (`http://localhost:8888/callback`) only works locally. If you ever deploy to Streamlit Cloud, the URI must be updated in both the Spotify dashboard and the secrets file.

### 9. Hardcoded Insomniac CSS selector

`get_event_lineup` uses `ul.lineup__list li` which is specific to Insomniac's HTML. Any other festival site will return 0 artists. Consider documenting this limitation or making the selector configurable.

---

## Running the App

```powershell
# Activate venv (once set up)
.venv\Scripts\activate

# Run locally
streamlit run app.py
```

Spotify will redirect to `http://localhost:8888/callback` after login — make sure this URI is registered in your Spotify developer dashboard.
