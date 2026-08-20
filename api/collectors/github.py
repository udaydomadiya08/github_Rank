import requests
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from api.config import settings
from api.database.models import Repository, RepositorySnapshot, CollectionRun
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
        from api.database.models import CrawlerState
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        repos = []
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
        
        # Get state
        state = self.db.query(CrawlerState).filter(CrawlerState.id == "singleton").first()
        if not state:
            state = CrawlerState(id="singleton", current_timeframe_index=0, current_page=1)
            self.db.add(state)
            self.db.commit()
            
        tf_index = state.current_timeframe_index
        if tf_index >= len(timeframes):
            tf_index = 0
            
        name, cutoff_date = timeframes[tf_index]
        
        query = "stars:>0"
        if cutoff_date:
            query += f" created:>{cutoff_date.strftime('%Y-%m-%dT%H:%M:%SZ')}"
            
        url = "https://api.github.com/search/repositories"
        logger.info(f"Fetching full timeframe concurrently: {name}")
        
        def fetch_page(page):
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": 100,
                "page": page
            }
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=8)
                if response.status_code == 200:
                    return response.json().get("items", [])
                elif response.status_code == 403:
                    logger.warning("GitHub API Error 403: Rate limit exceeded.")
            except Exception as e:
                logger.error(f"Network error during fetch page {page}: {e}")
            return []
            
        # Fetch all 5 pages (500 repos) simultaneously!
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_page = {executor.submit(fetch_page, page): page for page in range(1, 6)}
            for future in as_completed(future_to_page):
                page_repos = future.result()
                repos.extend(page_repos)
                
        if repos:
            # Advance to the next timeframe for the next execution
            state.current_timeframe_index = (tf_index + 1) % len(timeframes)
            self.db.commit()
            
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
