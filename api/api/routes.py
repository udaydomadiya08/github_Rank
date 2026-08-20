from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
import json
from datetime import datetime, timezone, timedelta

from api.database.connection import get_db
from api.database.models import Repository, CollectionRun, RepositorySnapshot
from api.ranking.engine import calculate_rankings
from api.collectors.github import run_collector

router = APIRouter()

@router.get("/cron/collect")
def cron_collect(db: Session = Depends(get_db)):
    run_collector(db)
    return {"status": "success"}

@router.get("/status")
def get_status(db: Session = Depends(get_db)):
    try:
        last_run = db.query(CollectionRun).order_by(desc(CollectionRun.id)).first()
        repo_count = db.query(func.count(Repository.id)).scalar()
        
        return {
            "status": "healthy" if last_run and last_run.status in ("completed", "running") else "error" if last_run and last_run.status == "error" else "unknown",
            "last_collection": last_run.completed_at if last_run else None,
            "repositories_tracked": repo_count,
            "api_requests_remaining": last_run.rate_limit_remaining if last_run else "Unknown",
            "last_run_status": last_run.status if last_run else None
        }
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}

def _parse_timeframe(tf: str) -> int:
    # Converts a string like '24h', '7d', '1m', '1y' into hours
    if tf == 'all':
        return 24 * 365 * 10 # 10 years roughly
    
    val = int(tf[:-1])
    unit = tf[-1].lower()
    if unit == 'h': return val
    if unit == 'd': return val * 24
    if unit == 'w': return val * 24 * 7
    if unit == 'm': return val * 24 * 30
    if unit == 'y': return val * 24 * 365
    return 24

def _get_enriched_repos(db: Session, tf: str = '24h', filter_created: bool = False):
    tf_hours = _parse_timeframe(tf)
    
    query = db.query(Repository).filter(Repository.archived == False)
    
    if filter_created and tf != 'all':
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=tf_hours)
        query = query.filter(Repository.created_at >= cutoff_date)
        
    repos = query.all()
    
    rankings = calculate_rankings(db, timeframe_hours=tf_hours)
    
    enriched = []
    for r in repos:
        r_dict = {
            "id": r.id,
            "full_name": r.full_name,
            "name": r.name,
            "owner": r.owner,
            "description": r.description,
            "html_url": r.html_url,
            "language": r.language,
            "topics": json.loads(r.topics) if r.topics else [],
            "stars": r.current_stars,
            "forks": r.current_forks,
            "updated_at": r.updated_at,
            "pushed_at": r.pushed_at
        }
        r_rank = rankings.get(r.id, {})
        r_dict.update({
            "velocity": r_rank.get("velocity", 0),
            "acceleration": r_rank.get("acceleration", 0),
            "momentum": r_rank.get("momentum", 0),
            "insufficient_data": r_rank.get("insufficient_data", True),
            "is_estimate": r_rank.get("is_estimate", False)
        })
        enriched.append(r_dict)
    return enriched

@router.get("/rankings/stars")
def get_ranking_stars(limit: int = 500, tf: str = '24h', db: Session = Depends(get_db)):
    repos = _get_enriched_repos(db, tf, filter_created=True)
    sorted_repos = sorted(repos, key=lambda x: x["stars"], reverse=True)
    return sorted_repos[:limit]

@router.get("/rankings/trending")
def get_ranking_trending(limit: int = 500, tf: str = '24h', db: Session = Depends(get_db)):
    repos = _get_enriched_repos(db, tf)
    # Trending based on velocity
    sorted_repos = sorted([r for r in repos if not r["insufficient_data"]], key=lambda x: x["velocity"], reverse=True)
    return sorted_repos[:limit]
    
@router.get("/rankings/emerging")
def get_ranking_emerging(limit: int = 500, max_stars: int = 15000, tf: str = '24h', db: Session = Depends(get_db)):
    repos = _get_enriched_repos(db, tf)
    # Emerging: high momentum but total stars under threshold
    emerging = [r for r in repos if r["stars"] < max_stars and not r["insufficient_data"]]
    sorted_repos = sorted(emerging, key=lambda x: x["momentum"], reverse=True)
    return sorted_repos[:limit]

@router.get("/rankings/momentum")
def get_ranking_momentum(limit: int = 500, tf: str = '24h', db: Session = Depends(get_db)):
    repos = _get_enriched_repos(db, tf)
    sorted_repos = sorted([r for r in repos if not r["insufficient_data"]], key=lambda x: x["momentum"], reverse=True)
    return sorted_repos[:limit]

@router.get("/repositories/{repo_id}")
def get_repository(repo_id: str, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
        
    rankings = calculate_rankings(db)
    r_rank = rankings.get(repo.id, {})
    
    return {
        "id": repo.id,
        "full_name": repo.full_name,
        "name": repo.name,
        "owner": repo.owner,
        "description": repo.description,
        "html_url": repo.html_url,
        "homepage": repo.homepage,
        "language": repo.language,
        "topics": json.loads(repo.topics) if repo.topics else [],
        "stars": repo.current_stars,
        "forks": repo.current_forks,
        "watchers": repo.current_watchers,
        "open_issues": repo.current_open_issues,
        "created_at": repo.created_at,
        "updated_at": repo.updated_at,
        "pushed_at": repo.pushed_at,
        "is_fork": repo.is_fork,
        "archived": repo.archived,
        "metrics": r_rank
    }

@router.get("/repositories/{repo_id}/history")
def get_repository_history(repo_id: str, db: Session = Depends(get_db)):
    snapshots = db.query(RepositorySnapshot)\
                  .filter(RepositorySnapshot.repository_id == repo_id)\
                  .order_by(RepositorySnapshot.recorded_at.asc())\
                  .all()
                  
    history = []
    for s in snapshots:
        history.append({
            "timestamp": s.recorded_at,
            "stars": s.stars,
            "forks": s.forks
        })
    return history
