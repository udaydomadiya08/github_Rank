import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base, Repository, RepositorySnapshot
from backend.ranking.engine import calculate_rankings

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_calculate_rankings_insufficient_data(db_session):
    repo = Repository(id="1", full_name="test/repo", current_stars=100)
    db_session.add(repo)
    
    # Only 1 snapshot
    snap1 = RepositorySnapshot(repository_id="1", stars=100, forks=10, recorded_at=datetime.now(timezone.utc))
    db_session.add(snap1)
    db_session.commit()
    
    rankings = calculate_rankings(db_session)
    assert rankings["1"]["insufficient_data"] is True
    assert rankings["1"]["momentum"] == 0

def test_calculate_rankings_velocity(db_session):
    now = datetime.now(timezone.utc)
    
    repo = Repository(id="2", full_name="test/repo2", current_stars=200)
    db_session.add(repo)
    
    # Snapshot 24h ago with 100 stars
    snap_old = RepositorySnapshot(repository_id="2", stars=100, forks=10, recorded_at=now - timedelta(hours=24))
    # Current snapshot with 200 stars
    snap_new = RepositorySnapshot(repository_id="2", stars=200, forks=20, recorded_at=now)
    
    db_session.add_all([snap_old, snap_new])
    db_session.commit()
    
    rankings = calculate_rankings(db_session)
    assert rankings["2"]["insufficient_data"] is False
    assert rankings["2"]["velocity_24h"] == 100.0
    assert rankings["2"]["fork_velocity_24h"] == 10.0
