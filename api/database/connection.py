from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from api.config import settings

db_url = settings.database_url
# We removed the pg8000 override to allow default psycopg2 to handle SSL properly

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
engine = create_engine(
    db_url, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
