# FestiBesti

Cross-reference any Insomniac festival lineup against your Spotify liked songs. Select a festival, log in with Spotify, and get a ranked table of lineup artists sorted by how many of their songs you've liked.

---

## Prerequisites

- Python 3.10+
- A [Spotify Developer](https://developer.spotify.com/dashboard) account with an app registered

---

## Setup

### 1. Clone the repo

```powershell
git clone <your-repo-url>
cd Spotify_Festival
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Spotify credentials

Create `.streamlit/secrets.toml` with your Spotify app credentials:

```toml
[my_secrets]
SPOTIPY_CLIENT_ID = "your_client_id"
SPOTIPY_CLIENT_SECRET = "your_client_secret"
SPOTIPY_REDIRECT_URI = "http://127.0.0.1:8501/"
```

In the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), add `http://127.0.0.1:8501/` as an allowed Redirect URI for your app.

### 5. Run the app

```powershell
streamlit run app.py
```

The app will open at `http://127.0.0.1:8501/` in your browser.

---

## Usage

1. Select a festival from the dropdown (or choose "Other" and paste any Insomniac lineup URL).
2. Click the Spotify login link and authorize the app.
3. After redirecting back, the app displays a table of lineup artists ranked by your liked song count.

---

## Deploying to Streamlit Cloud

1. Push the repo to GitHub.
2. Connect the repo in [Streamlit Cloud](https://streamlit.io/cloud).
3. Add your secrets in the Streamlit Cloud dashboard under **App settings → Secrets** (same format as `secrets.toml`).
4. Update `SPOTIPY_REDIRECT_URI` to your deployed app URL (e.g. `https://festibestiapp.streamlit.app`), and register that URI in the Spotify Developer Dashboard as well.
