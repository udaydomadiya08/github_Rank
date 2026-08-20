# Architecture

## Overview
GitHub LiveRank uses a decoupled client-server architecture with a local SQLite database for persistence.

### Backend (Python/FastAPI)
- **FastAPI**: Serves RESTful endpoints for the frontend.
- **APScheduler**: Runs a background job (default: every 5 mins) to poll the GitHub API.
- **GitHub Collector**: Batches requests to the GitHub Search and Repositories API, handling pagination and rate limiting (using `X-RateLimit` headers).
- **SQLite + SQLAlchemy**: Stores normalized `repositories` and time-series `repository_snapshots`.

### Frontend (React/Vite)
- **React + TypeScript**: Provides a robust, type-safe UI.
- **Tailwind CSS**: Used for styling the vibrant, dark-themed dashboard.
- **useApi Hook**: Handles data fetching and polling to keep the dashboard "Live" without needing manual refreshes.

### Data Flow
1. **Background Collection**: APScheduler triggers the collector -> Fetches from GitHub API -> Updates DB.
2. **Dashboard Render**: React frontend requests `/api/rankings/*`.
3. **Ranking Engine**: FastAPI queries the SQLite DB, compares the latest snapshot against 1h, 24h, and 48h old snapshots, calculates scores, and returns JSON.
