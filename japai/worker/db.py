from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from worker.config import worker_settings

engine = create_engine(worker_settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Session:
    """Returns a new SQLAlchemy session for the worker."""
    return SessionLocal()
