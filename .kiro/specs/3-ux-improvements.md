# Spec: UX Improvements & User Guidance

## Overview

The current app drops the user into a selectbox with no context about what the app does or what they need to do next. This spec covers adding onboarding content, improving the flow between steps, and making the results table more useful.

## Requirements

### 1. App introduction
- The app must display a brief description of what it does above the festival selector
- The description must be visible before the user logs in

### 2. Step-by-step flow indicators
- The UI must make the two-step process explicit: (1) pick a festival, (2) log in with Spotify
- The login link must only appear after a festival is selected (already implemented via the `if event_url` guard)
- A visual or textual cue must indicate what will happen after login (i.e., "we'll compare the lineup against your liked songs")

### 3. Loading feedback
- While the app is fetching the lineup and liked songs, a progress indicator must be shown
- The current `st.write(...)` status messages should be replaced with `st.status(...)` or `st.spinner(...)` for a cleaner look
- The total liked songs count should be displayed in the results section, not as a mid-load message

### 4. Results table improvements
- The results table must show the festival name or URL being compared in a header above the table
- Artists with 0 liked songs must still appear in the table (already implemented) but visually de-emphasized or filterable
- A summary stat must be shown above the table: e.g., "X of Y artists have at least one liked song"

### 5. Error and empty state messaging
- Error messages (already added) must be styled consistently using `st.error()`
- The "no artists found" case must explain the likely cause (lineup not announced, wrong URL)
- The "no liked songs" case must suggest the user check they logged into the correct Spotify account

### 6. Re-run / switch festival
- After results are shown, the user must be able to return to the festival selector without a full page refresh
- A "Check another festival" button must clear the current results and show the selector again

## Out of Scope

- User accounts or saved preferences
- Sorting or filtering beyond what Streamlit's `st.dataframe` provides natively
- Mobile-specific layout changes
