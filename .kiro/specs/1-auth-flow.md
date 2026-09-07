# Spec: Fix Auth Flow

## Overview

The current Spotify OAuth flow forces a full re-authentication on every Streamlit rerun (any widget interaction, page refresh, etc.). This spec covers caching the token in `st.session_state` so users authenticate once per browser session, supporting multiple concurrent users safely.

## Requirements

### 1. Session-scoped token caching
- After a successful OAuth exchange, the token must be stored in `st.session_state["token_info"]`
- On every rerun, the app must check `st.session_state` for a valid token before running the OAuth flow
- If a token exists in session state but is expired, the app must silently refresh it using `auth_manager.refresh_access_token()` and update session state
- No token data may be written to disk — file-based caching (`.cache`) is explicitly excluded to prevent cross-user token leakage on shared deployments

### 2. Multi-user safety
- Each browser session has its own isolated `st.session_state` — tokens must never be shared between users
- The app must not use any server-side shared storage (disk, database, global variables) for token data
- Closing the tab or ending the browser session clears the token naturally

### 3. Reduce re-auth friction
- `show_dialog=True` must be changed to `show_dialog=False` so Spotify only prompts login when there is no valid session
- `check_cache=False` can be removed since file-based caching is no longer used

### 4. Festival selection with cached auth
- When a valid token exists in session state, the festival selector must be shown without redirecting to Spotify
- The user must be able to switch festivals and re-run the comparison without re-authenticating
- The OAuth `state` param approach (encoding the festival URL) is still used for the initial auth redirect, and the decoded URL must be stored in `st.session_state["event_url"]` alongside the token

### 5. Logout
- A "Log out" button must be provided that clears `st.session_state["token_info"]` and `st.session_state["event_url"]`
- After logout the app must return to the unauthenticated state showing the festival selector and login link

### 6. Auth state display
- When a valid token exists, the authenticated user's Spotify display name must be shown
- The login link must only appear when no valid token is in session state

## Technical Notes

- `auth_manager.is_token_expired(token_info)` checks expiry
- `auth_manager.refresh_access_token(token_info["refresh_token"])` returns a new token dict
- Streamlit reruns the entire script on every interaction — all auth checks must be at the top of the main flow so the correct UI branch is rendered consistently
- The `?code=` query param is only present on the initial OAuth redirect; subsequent reruns will not have it, so session state is the only reliable auth signal after first login

## Out of Scope

- Remembering the user across browser sessions (would require server-side storage)
- Switching Spotify accounts without logging out first
- File-based token caching (`.cache`)
