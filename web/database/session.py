"""
Database session management for PROSIM web interface.

Provides SQLAlchemy session factory and dependency injection
helpers for FastAPI.
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from web.config import get_settings
from web.database.models import Base

# Engine and session factory (initialized lazily)
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        config = get_settings()

        # Ensure data directory exists for SQLite
        if config.database_url.startswith("sqlite"):
            db_path = config.database_url.replace("sqlite:///", "")
            if db_path.startswith("./"):
                db_path = db_path[2:]
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        _engine = create_engine(
            config.database_url,
            connect_args={"check_same_thread": False}  # Needed for SQLite
            if config.database_url.startswith("sqlite")
            else {},
            echo=config.debug,
        )
    return _engine


def get_session_factory() -> sessionmaker:
    """Get or create the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _SessionLocal


def init_db() -> None:
    """Initialize the database by creating all tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session.

    Usage in routes:
        @router.get("/")
        async def index(db: Session = Depends(get_db)):
            ...
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database sessions outside of FastAPI.

    Usage:
        with get_db_context() as db:
            games = db.query(GameSession).all()
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
