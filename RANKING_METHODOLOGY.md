# Ranking Methodology

The core feature of GitHub LiveRank is its ability to identify trends using historical snapshots rather than just absolute totals.

## Core Metrics

### 1. Velocity (Stars/hour)
Calculated by taking the difference in stars over a specific time window.
- **24h Velocity**: `(Current Stars - Stars 24h ago) / (Hours Difference)`

### 2. Acceleration
Measures the change in velocity, identifying repositories that are "speeding up".
- **Acceleration**: `(Current 24h Velocity) - (Previous 24h Velocity)` (where Previous is the window from 48h ago to 24h ago).

### 3. Momentum Score
A composite score out of 100 indicating the current "heat" of a repository.
- **Raw Formula**: `(0.4 * Star Velocity) + (0.2 * Acceleration) + (0.15 * Fork Velocity) + (Recency Boost)`
- The raw score is then min-max normalized across all currently tracked repositories to provide a clean 0-100 scale.

### 4. Emerging Status
A repository is considered "Emerging" if it has high Momentum but its total star count is under a specific threshold (e.g., < 15,000 stars). This highlights hidden gems before they reach the absolute top of the global leaderboards.
