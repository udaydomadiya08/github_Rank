# GitHub LiveRank

GitHub LiveRank is a Bloomberg Terminal-style intelligence dashboard for the GitHub ecosystem. It allows you to discover, rank, monitor, and analyze repositories in near-real-time.

## Features
- **Real-time Collection**: Periodically polls the GitHub API to update top repositories.
- **Historical Snapshots**: Maintains time-series data to calculate trends and momentum.
- **Advanced Ranking**: Sorts by total stars, 24h growth (Trending), Momentum, and Emerging status.
- **Momentum Engine**: Detects acceleration and velocity of repository growth.
- **Modern Dashboard**: Built with React, Vite, and Tailwind CSS.

## Setup Instructions

### 1. Configure Environment
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Add your personal GitHub Token to `.env` (without quotes):
   ```
   GITHUB_TOKEN=ghp_your_token_here
   ```

### 2. Run the Application
Start both the backend API (with background collector) and the frontend dashboard.

**Terminal 1 (Backend):**
```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

### 3. Usage
Open `http://localhost:5173` in your browser. 
The background collector will immediately start fetching the top repositories and will repeat every 5 minutes (configurable in `.env`).

## Note on Rate Limits
The application is designed to handle GitHub rate limits gracefully. If the limit is reached, it will pause collection until the reset time.
