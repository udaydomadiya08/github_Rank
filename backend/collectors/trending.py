import requests
import time
import logging
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import json

from backend.config import settings
from backend.database.models import Repository, RepositorySnapshot

logger = logging.getLogger(__name__)

class TrendingCollector:
    def __init__(self, db: Session):
        self.db = db
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if settings.github_token:
            self.headers["Authorization"] = f"token {settings.github_token}"

    def run(self):
        logger.info("Starting GitHub Trending Collection...")
        
        timeframes = [
            ('daily', 24),
            ('weekly', 24 * 7),
            ('monthly', 24 * 30)
        ]
        
        seen_repos = set()
        
        for tf_name, tf_hours in timeframes:
            logger.info(f"Scraping trending {tf_name}...")
            url = f"https://github.com/trending?since={tf_name}"
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Failed to fetch trending {tf_name}: {e}")
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('article', class_='Box-row')
            
            for article in articles:
                h2 = article.find('h2', class_='h3')
                if not h2:
                    continue
                
                # Parse "owner / name"
                full_name_raw = h2.text.strip().replace(' ', '').replace('\n', '')
                if '/' not in full_name_raw:
                    continue
                    
                owner, name = full_name_raw.split('/', 1)
                full_name = f"{owner}/{name}"
                
                if full_name in seen_repos:
                    continue
                
                # Parse delta stars
                stars_span = article.find('span', class_='d-inline-block float-sm-right')
                delta_stars = 0
                if stars_span:
                    stars_text = stars_span.text.strip()
                    # Example: "1,234 stars today"
                    digits = ''.join(c for c in stars_text if c.isdigit())
                    if digits:
                        delta_stars = int(digits)
                
                if delta_stars > 0:
                    self._process_trending_repo(full_name, owner, name, delta_stars, tf_hours)
                    seen_repos.add(full_name)

    def _process_trending_repo(self, full_name, owner, name, delta_stars, tf_hours):
        # 1. Check if repo exists in DB
        repo = self.db.query(Repository).filter(Repository.full_name == full_name).first()
        
        # 2. If not, fetch from API
        if not repo:
            url = f"https://api.github.com/repos/{full_name}"
            while True:
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    
                    try:
                        repo = Repository(
                            id=str(data["id"]),
                            full_name=full_name,
                            name=name,
                            owner=owner,
                            description=data.get("description"),
                            html_url=data.get("html_url"),
                            language=data.get("language"),
                            topics=json.dumps(data.get("topics", [])),
                            created_at=datetime.strptime(data["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc),
                            updated_at=datetime.strptime(data["updated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc),
                            pushed_at=datetime.strptime(data["pushed_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc),
                            current_stars=data.get("stargazers_count", 0),
                            current_forks=data.get("forks_count", 0)
                        )
                        self.db.add(repo)
                        self.db.commit()
                        logger.info(f"Added trending repo: {full_name}")
                    except IntegrityError:
                        self.db.rollback()
                        repo = self.db.query(Repository).filter(Repository.full_name == full_name).first()
                        
                    if "Authorization" not in self.headers:
                        time.sleep(6.5)
                    break
                elif response.status_code == 401:
                    logger.warning("GitHub API Error 401: Bad credentials. Falling back to unauthenticated requests.")
                    if "Authorization" in self.headers:
                        del self.headers["Authorization"]
                    time.sleep(2)
                    continue
                elif response.status_code == 403:
                    logger.warning("Rate limit on repo fetch. Sleeping 60s...")
                    time.sleep(60)
                elif response.status_code == 404:
                    logger.warning(f"Repo {full_name} not found in API.")
                    break
                else:
                    logger.error(f"Error fetching repo {full_name}: {response.status_code}")
                    break
                    
        if not repo:
            return
            
        # 3. Create synthetic snapshot for `now - tf_hours`
        historical_time = datetime.now(timezone.utc) - timedelta(hours=tf_hours)
        historical_stars = repo.current_stars - delta_stars
        
        # Check if snapshot near this time already exists
        # To avoid cluttering, we only add a synthetic snapshot if one doesn't exist within 1 hour
        time_lower = historical_time - timedelta(hours=1)
        time_upper = historical_time + timedelta(hours=1)
        
        existing = self.db.query(RepositorySnapshot).filter(
            RepositorySnapshot.repository_id == repo.id,
            RepositorySnapshot.recorded_at >= time_lower,
            RepositorySnapshot.recorded_at <= time_upper
        ).first()
        
        if not existing:
            snapshot = RepositorySnapshot(
                repository_id=repo.id,
                stars=historical_stars,
                forks=repo.current_forks, # Delta forks not available, keep current
                recorded_at=historical_time
            )
            self.db.add(snapshot)
            try:
                self.db.commit()
                logger.info(f"Added synthetic snapshot for {full_name}: {historical_stars} stars at {historical_time}")
            except Exception as e:
                self.db.rollback()
                logger.error(f"Error adding snapshot for {full_name}: {e}")

def run_trending_collector(db: Session):
    collector = TrendingCollector(db)
    collector.run()
