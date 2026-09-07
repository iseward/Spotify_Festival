# Spec: Publish App to Streamlit Cloud

## Overview

Deploy FestiBesti to Streamlit Cloud so it can be shared with friends via a public URL (`https://FestiBestiApp.streamlit.app`). This covers the deployment configuration, secrets management, and the process for keeping the live app updated.

## Requirements

### 1. Streamlit Cloud deployment
- The app must be deployable from the GitHub repo connected to Streamlit Cloud
- The `main` (or designated deploy) branch must always contain a working version of the app
- Streamlit Cloud must be configured to redeploy automatically when the deploy branch is updated

### 2. Secrets management
- Spotify credentials must be stored in Streamlit Cloud's secrets manager, not committed to the repo
- The secrets format in Streamlit Cloud must match the local `.streamlit/secrets.toml` structure (`[my_secrets]` with `client_id`, `client_secret`, `redirect_uri`)
- The deployed `redirect_uri` must be `https://FestiBestiApp.streamlit.app` (already registered in Spotify dashboard)
- Local `secrets.toml` uses `http://127.0.0.1:8501/` — these are separate configs, not to be mixed

### 3. Keeping the app updated
- The workflow is: develop on `Dev` branch → merge to `main` → Streamlit Cloud auto-redeploys
- No manual deployment steps should be required beyond the git merge

### 4. Spotify app user allowlist
- Streamlit Cloud deployment is still subject to Spotify's Development Mode 25-user cap
- Each friend who wants to use the app must have their Spotify account email manually added to the allowlist in the Spotify Developer Dashboard
- There is no automated workaround for this cap (see backlog note below)

## Deployment Steps (one-time setup)

1. Push repo to GitHub if not already there
2. Connect repo to Streamlit Cloud at share.streamlit.io
3. Set deploy branch and entry point (`app.py`)
4. Add Spotify credentials to Streamlit Cloud secrets manager
5. Verify `https://FestiBestiApp.streamlit.app` is in the Spotify dashboard redirect URIs

## Backlog: Auto-adding beta users (2a)

Spotify's Development Mode requires manual allowlisting of each user in the Spotify Developer Dashboard. As of May 2025, Extended Quota Mode (which removes this cap) requires 250k MAUs and an established business entity — not applicable here.

No automated solution exists within Spotify's current API policies. The only options are:
- Manual allowlisting (current approach, max 25 users)
- Apply for Extended Quota Mode if/when eligibility criteria are met

## Out of Scope

- Custom domain setup
- CI/CD pipelines beyond the Streamlit Cloud auto-redeploy
- Analytics or usage tracking
