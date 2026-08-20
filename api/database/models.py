from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from api.database.connection import Base
from datetime import datetime, timezone

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String, primary_key=True, index=True) # GitHub ID as string
    full_name = Column(String, index=True)
    owner = Column(String, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    html_url = Column(String)
    homepage = Column(String, nullable=True)
    language = Column(String, index=True, nullable=True)
    topics = Column(String, nullable=True) # Stored as JSON string
    license = Column(String, nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    pushed_at = Column(DateTime)
    archived = Column(Boolean, default=False)
    is_fork = Column(Boolean, default=False)
    
    current_stars = Column(Integer, index=True, default=0)
    current_forks = Column(Integer, default=0)
    current_watchers = Column(Integer, default=0)
    current_open_issues = Column(Integer, default=0)

class RepositorySnapshot(Base):
    __tablename__ = "repository_snapshots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(String, index=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    stars = Column(Integer)
    forks = Column(Integer)
    watchers = Column(Integer)
    open_issues = Column(Integer)

class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    repositories_requested = Column(Integer, default=0)
    repositories_updated = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    rate_limit_remaining = Column(Integer, default=0)
    status = Column(String, default="running")
