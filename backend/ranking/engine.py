import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from datetime import datetime, timedelta, timezone
from backend.database.models import Repository, RepositorySnapshot

def calculate_rankings(db: Session, timeframe_hours: int = 24):
    """
    Calculates velocity, acceleration, and momentum for all repositories over a specific timeframe.
    Returns a dictionary of metrics per repository_id.
    """
    now = datetime.now(timezone.utc)
    
    # We need snapshots for the target timeframe and the previous timeframe (to calculate acceleration)
    target_time = now - timedelta(hours=timeframe_hours)
    prev_target_time = now - timedelta(hours=timeframe_hours * 2)
    
    # Fetch all repositories
    repos = db.query(Repository).filter(Repository.archived == False).all()
    
    results = {}
    
    for repo in repos:
        # Get snapshots for this repo ordered by time descending
        snapshots = db.query(RepositorySnapshot)\
                      .filter(RepositorySnapshot.repository_id == repo.id)\
                      .order_by(RepositorySnapshot.recorded_at.desc())\
                      .all()
                      
        # Safe fallback for days since creation
        repo_created_at = repo.created_at.replace(tzinfo=timezone.utc) if repo.created_at else now - timedelta(days=365)
        days_since_creation = max(1, (now - repo_created_at).days)
        estimated_stars_per_hour = repo.current_stars / (days_since_creation * 24.0)
        estimated_forks_per_hour = repo.current_forks / (days_since_creation * 24.0)
                      
        if not snapshots or len(snapshots) < 1:
            # Fallback entirely to estimates if no snapshots exist at all
            vel = estimated_stars_per_hour * timeframe_hours
            results[repo.id] = {
                "velocity": round(vel, 2),
                "acceleration": 0,
                "momentum_raw": vel * 0.4, # Basic momentum
                "fork_velocity": round(estimated_forks_per_hour * timeframe_hours, 2),
                "insufficient_data": False,
                "is_estimate": True
            }
            continue
            
        current = snapshots[0]
        
        # Find snapshot closest to target_time
        snap_target = _closest_snapshot(snapshots, target_time)
        
        # Find snapshot closest to prev_target_time
        snap_prev = _closest_snapshot(snapshots, prev_target_time)
        
        # Velocity calculations
        vel = 0
        is_estimate = False
        
        if snap_target and (snap_target.recorded_at.replace(tzinfo=timezone.utc) < now - timedelta(hours=timeframe_hours * 0.5)):
            # We have a reasonably old snapshot to use real data
            hours_diff = (current.recorded_at.replace(tzinfo=timezone.utc) - snap_target.recorded_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
            if hours_diff > 0:
                vel_per_hour = (current.stars - snap_target.stars) / hours_diff
                vel = vel_per_hour * timeframe_hours
        else:
            # Fallback to estimate if we don't have enough history for the requested timeframe
            vel = estimated_stars_per_hour * timeframe_hours
            is_estimate = True
                
        prev_vel = 0
        if snap_target and snap_prev and not is_estimate:
            hours_diff_prev = (snap_target.recorded_at.replace(tzinfo=timezone.utc) - snap_prev.recorded_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
            if hours_diff_prev > 0:
                prev_vel_per_hour = (snap_target.stars - snap_prev.stars) / hours_diff_prev
                prev_vel = prev_vel_per_hour * timeframe_hours
        else:
            # Assume constant velocity for estimate
            prev_vel = vel
                
        acceleration = vel - prev_vel
        
        fork_vel = 0
        if snap_target and not is_estimate:
            hours_diff = (current.recorded_at.replace(tzinfo=timezone.utc) - snap_target.recorded_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
            if hours_diff > 0:
                fork_vel_per_hour = (current.forks - snap_target.forks) / hours_diff
                fork_vel = fork_vel_per_hour * timeframe_hours
        else:
            fork_vel = estimated_forks_per_hour * timeframe_hours

        # Baseline Momentum Score (Unnormalized)
        # 40% star velocity + 20% star acceleration + 15% fork velocity
        momentum_raw = (0.4 * vel) + (0.2 * acceleration) + (0.15 * fork_vel)
        
        # Recency boost (up to 5%): Repos pushed recently get a small bump
        recency_boost = 0
        if repo.pushed_at:
            days_since_push = (now - repo.pushed_at.replace(tzinfo=timezone.utc)).days
            if days_since_push < 7:
                recency_boost = 5 * (1 - days_since_push/7)
                
        momentum_raw += recency_boost
                
        results[repo.id] = {
            "velocity": round(vel, 2),
            "acceleration": round(acceleration, 2),
            "momentum_raw": momentum_raw,
            "fork_velocity": round(fork_vel, 2),
            "insufficient_data": False,
            "is_estimate": is_estimate
        }

    # Normalize momentum score to 0-100 range
    valid_scores = [v["momentum_raw"] for v in results.values() if not v["insufficient_data"]]
    
    if valid_scores:
        min_score = min(valid_scores)
        max_score = max(valid_scores)
        score_range = max_score - min_score if max_score > min_score else 1
        
        for k, v in results.items():
            if not v["insufficient_data"]:
                normalized = ((v["momentum_raw"] - min_score) / score_range) * 100
                v["momentum"] = round(normalized, 1)
            else:
                v["momentum"] = 0
                
    return results

def _closest_snapshot(snapshots, target_time):
    # Snapshots are ordered descending (newest first)
    # Find the snapshot whose recorded_at is closest to target_time
    closest = None
    min_diff = float('inf')
    
    for s in snapshots:
        diff = abs((s.recorded_at.replace(tzinfo=timezone.utc) - target_time).total_seconds())
        if diff < min_diff:
            min_diff = diff
            closest = s
            
    return closest
