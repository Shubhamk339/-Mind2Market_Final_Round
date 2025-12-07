"""
Database configuration and session management using SQLAlchemy.
"""

import os
import tempfile
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database file path
# Streamlit Cloud runs in a read-only filesystem, so we need to use a writable location
# Check if running on Streamlit Cloud (STREAMLIT_SHARING_MODE is set in cloud environment)
if os.environ.get("STREAMLIT_SHARING_MODE") or os.environ.get("STREAMLIT_SERVER_HEADLESS"):
    # Use temp directory for Streamlit Cloud
    DB_PATH = os.path.join(tempfile.gettempdir(), "trading_simulation.db")
else:
    # Local development
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trading_simulation.db")

DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

# Create session factory
# expire_on_commit=False prevents DetachedInstanceError when accessing objects after session closes
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

# Base class for models
Base = declarative_base()


def init_db():
    """Initialize the database by creating all tables."""
    from . import models  # Import models to register them
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session():
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_db_session():
    """Get a new database session (for use without context manager)."""
    return SessionLocal()
