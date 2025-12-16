"""
Database configuration and session management using SQLAlchemy.
"""

import os
import tempfile
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import streamlit as st

# Database Selection Logic
# 1. Try to get DATABASE_URL from Streamlit secrets (for Cloud/Local with secrets)
# 2. Try to get DATABASE_URL from environment variables (for Docker/Vercel)
# 3. Fallback to SQLite (localdev/testing)

if "DATABASE_URL" in st.secrets:
    DATABASE_URL = st.secrets["DATABASE_URL"]
elif "DATABASE_URL" in os.environ:
    DATABASE_URL = os.environ["DATABASE_URL"]
else:
    # Local development fallback
    if os.environ.get("STREAMLIT_SHARING_MODE") or os.environ.get("STREAMLIT_SERVER_HEADLESS"):
         DB_PATH = os.path.join(tempfile.gettempdir(), "trading_simulation.db")
    else:
         DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trading_simulation.db")
    DATABASE_URL = f"sqlite:///{DB_PATH}"

# Fix for "postgres://" in SQLAlchemy (needs "postgresql://")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine
# valid_connect_args for SQLite only
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

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
