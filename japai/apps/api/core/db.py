import logging
import re
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from apps.api.core.config import settings

logger = logging.getLogger("ja_assure.db")


def _build_engine():
    raw_url = settings.DATABASE_URL
    urls_to_try = [raw_url]

    # If Supabase direct connection is detected, generate IPv4 pooler URLs
    match = re.search(r"db\.([a-z0-9]+)\.supabase\.co", raw_url)
    if match:
        ref = match.group(1)
        # Pooler port 6543 (transaction)
        pooler_url_6543 = re.sub(
            r"://([^:]+):([^@]+)@db\.[a-z0-9]+\.supabase\.co:\d+/(.+)",
            r"://\1." + ref + r":\2@aws-0-ap-southeast-1.pooler.supabase.com:6543/\3?sslmode=require",
            raw_url,
        )
        # Pooler port 5432 (session)
        pooler_url_5432 = re.sub(
            r"://([^:]+):([^@]+)@db\.[a-z0-9]+\.supabase\.co:\d+/(.+)",
            r"://\1." + ref + r":\2@aws-0-ap-southeast-1.pooler.supabase.com:5432/\3?sslmode=require",
            raw_url,
        )
        # General pooler
        pooler_url_general = re.sub(
            r"://([^:]+):([^@]+)@db\.[a-z0-9]+\.supabase\.co:\d+/(.+)",
            r"://\1." + ref + r":\2@pooler.supabase.com:6543/\3?sslmode=require",
            raw_url,
        )
        urls_to_try = [pooler_url_6543, pooler_url_5432, pooler_url_general, raw_url]

    for candidate_url in urls_to_try:
        try:
            connect_args = {"connect_timeout": 5} if "postgresql" in candidate_url else {}
            eng = create_engine(candidate_url, pool_pre_ping=True, connect_args=connect_args)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to database with candidate URL.")
            return eng
        except Exception as e:
            logger.warning("Failed connecting to candidate database: %s", e)

    # If all remote database connections fail, fall back to SQLite
    logger.error("All PostgreSQL connections failed. Falling back to SQLite.")
    sqlite_url = "sqlite:///./ja_assure.db"
    return create_engine(sqlite_url, connect_args={"check_same_thread": False})


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
