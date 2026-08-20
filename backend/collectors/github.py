import requests
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from backend.config import settings
from backend.database.models import Repository, RepositorySnapshot, CollectionRun
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class GitHubCollector:
    def __init__(self, db: Session):
        self.db = db
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if settings.github_token:
            self.headers["Authorization"] = f"token {settings.github_token}"
            
    def fetch_top_repositories(self, limit: int = 500) -> list:
        repos = []
        
        # We will fetch top 100 repos for each major timeframe to ensure we have data 
        # for "Top repos created in the last X duration"
        now = datetime.now(timezone.utc)
        timeframes = [
            ("All Time", None),
            ("5 Years", now - timedelta(days=365*5)),
            ("3 Years", now - timedelta(days=365*3)),
            ("1 Year", now - timedelta(days=365)),
            ("6 Months", now - timedelta(days=30*6)),
            ("3 Months", now - timedelta(days=30*3)),
            ("1 Month", now - timedelta(days=30)),
            ("7 Days", now - timedelta(days=7)),
            ("24 Hours", now - timedelta(days=1))
        ]
        
        for name, cutoff_date in timeframes:
            query = "stars:>0"
            if cutoff_date:
                query += f" created:>{cutoff_date.strftime('%Y-%m-%dT%H:%M:%SZ')}"
                
            url = "https://api.github.com/search/repositories"
            logger.info(f"Fetching top 500 repos for timeframe: {name}")
            
            for page in range(1, 6):
                params = {
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 100,
                    "page": page
                }
                
                items_found = False
                while True:
                    try:
                        response = requests.get(url, headers=self.headers, params=params)
                        
                        if response.status_code == 200:
                            data = response.json()
                            items = data.get("items", [])
                            repos.extend(items)
                            
                            if items:
                                items_found = True
                            
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
                            logger.warning("GitHub API Error 403: Rate limit exceeded. Backing off for 60 seconds.")
                            time.sleep(60)
                            continue
                        else:
                            logger.error(f"GitHub API Error {response.status_code}: {response.text}")
                            break
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Network error during fetch: {e}")
                        break
                        
                if not items_found:
                    break
                
        return repos
        
    def _handle_rate_limit(self, response: requests.Response):
        remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
        reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
        
        if remaining == 0:
            sleep_time = max(reset_time - time.time(), 0) + 1
            logger.warning(f"Rate limit hit. Sleeping for {sleep_time} seconds.")
            time.sleep(sleep_time)

    def process_repositories(self, repos_data: list, run_record: CollectionRun):
        updated_count = 0
        error_count = 0
        seen_repos = set()
        
        for repo_data in repos_data:
            try:
                repo_id = str(repo_data["id"])
                
                if repo_id in seen_repos:
                    continue
                seen_repos.add(repo_id)
                
                # Check if repo exists
                repo = self.db.query(Repository).filter(Repository.id == repo_id).first()
                
                created_at = datetime.strptime(repo_data["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                updated_at = datetime.strptime(repo_data["updated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                pushed_at = datetime.strptime(repo_data["pushed_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                
                if not repo:
                    repo = Repository(
                        id=repo_id,
                        full_name=repo_data.get("full_name"),
                        owner=repo_data.get("owner", {}).get("login"),
                        name=repo_data.get("name"),
                        description=repo_data.get("description"),
                        html_url=repo_data.get("html_url"),
                        homepage=repo_data.get("homepage"),
                        language=repo_data.get("language"),
                        topics=json.dumps(repo_data.get("topics", [])),
                        license=repo_data.get("license", {}).get("name") if repo_data.get("license") else None,
                        created_at=created_at,
                        updated_at=updated_at,
                        pushed_at=pushed_at,
                        archived=repo_data.get("archived", False),
                        is_fork=repo_data.get("fork", False),
                    )
                    self.db.add(repo)
                else:
                    repo.full_name = repo_data.get("full_name")
                    repo.description = repo_data.get("description")
                    repo.language = repo_data.get("language")
                    repo.topics = json.dumps(repo_data.get("topics", []))
                    repo.updated_at = updated_at
                    repo.pushed_at = pushed_at
                    repo.archived = repo_data.get("archived", False)
                
                # Update current stats
                repo.current_stars = repo_data.get("stargazers_count", 0)
                repo.current_forks = repo_data.get("forks_count", 0)
                repo.current_watchers = repo_data.get("watchers_count", 0)
                repo.current_open_issues = repo_data.get("open_issues_count", 0)
                
                # Add Snapshot
                snapshot = RepositorySnapshot(
                    repository_id=repo_id,
                    stars=repo.current_stars,
                    forks=repo.current_forks,
                    watchers=repo.current_watchers,
                    open_issues=repo.current_open_issues
                )
                self.db.add(snapshot)
                
                updated_count += 1
            except Exception as e:
                logger.error(f"Error processing repo {repo_data.get('full_name')}: {e}")
                error_count += 1
                
        self.db.commit()
        run_record.repositories_updated = updated_count
        run_record.errors = error_count

    def run(self):
        logger.info("Starting collection run...")
        run_record = CollectionRun(repositories_requested=settings.max_repositories)
        self.db.add(run_record)
        self.db.commit()
        
        repos = self.fetch_top_repositories(limit=settings.max_repositories)
        
        self.process_repositories(repos, run_record)
        
        run_record.completed_at = datetime.now(timezone.utc)
        run_record.status = "completed"
        
        # Determine remaining rate limit by making a dummy request or relying on last response
        try:
            resp = requests.get("https://api.github.com/rate_limit", headers=self.headers, timeout=5)
            if resp.status_code == 200:
                run_record.rate_limit_remaining = resp.json().get("rate", {}).get("remaining", 0)
        except Exception:
            pass
            
        self.db.commit()
        logger.info(f"Collection run completed. Updated {run_record.repositories_updated} repos.")

def run_collector(db: Session):
    collector = GitHubCollector(db)
    collector.run()
