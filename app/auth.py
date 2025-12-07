"""
Authentication utilities for the trading simulation application.
"""

import bcrypt
import streamlit as st
from .database import get_session
from .models import Team


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def login_user(username: str, password: str) -> dict:
    """
    Attempt to log in a user.
    Returns dict with success status and user info or error message.
    """
    with get_session() as session:
        team = session.query(Team).filter(Team.username == username).first()
        
        if not team:
            return {"success": False, "error": "Invalid username or password"}
        
        if not verify_password(password, team.password_hash):
            return {"success": False, "error": "Invalid username or password"}
        
        return {
            "success": True,
            "team_id": team.id,
            "team_name": team.name,
            "industry": team.industry,
            "is_admin": team.is_admin
        }


def logout_user():
    """Clear session state for logout."""
    keys_to_clear = ["team_id", "team_name", "industry", "is_admin", "authenticated"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return st.session_state.get("authenticated", False)


def is_admin() -> bool:
    """Check if current user is an admin."""
    return st.session_state.get("is_admin", False)


def get_current_team_id() -> int:
    """Get the current logged-in team's ID."""
    return st.session_state.get("team_id")


def get_current_team_name() -> str:
    """Get the current logged-in team's name."""
    return st.session_state.get("team_name", "")


def get_current_team_industry() -> str:
    """Get the current logged-in team's industry."""
    return st.session_state.get("industry", "")


def require_auth(func):
    """Decorator to require authentication for a function."""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.error("Please log in to access this page.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def require_admin(func):
    """Decorator to require admin privileges for a function."""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.error("Please log in to access this page.")
            st.stop()
        if not is_admin():
            st.error("Admin privileges required.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper
