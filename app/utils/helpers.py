"""
Helper utility functions for the trading simulation application.
"""

from typing import List
from .constants import INDUSTRIES


def format_currency(amount: float) -> str:
    """Format amount as Indian Rupees."""
    return f"₹{amount:,.2f}"


def get_other_industries(industry: str) -> List[str]:
    """Get list of all industries except the specified one."""
    return [ind for ind in INDUSTRIES if ind != industry]


def validate_positive_integer(value: int, field_name: str) -> bool:
    """Validate that a value is a positive integer."""
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return True


def validate_non_negative_float(value: float, field_name: str) -> bool:
    """Validate that a value is a non-negative float."""
    if value < 0:
        raise ValueError(f"{field_name} cannot be negative")
    return True


def get_industry_emoji(industry: str) -> str:
    """Get emoji for each industry."""
    emoji_map = {
        "Cement": "🏗️",
        "Energy": "⚡",
        "Iron": "🔩",
        "Aluminium": "🔧",
        "Wood": "🪵"
    }
    return emoji_map.get(industry, "📦")


def get_industry_color(industry: str) -> str:
    """Get color for each industry."""
    color_map = {
        "Cement": "#808080",
        "Energy": "#FFD700",
        "Iron": "#8B4513",
        "Aluminium": "#C0C0C0",
        "Wood": "#8B4513"
    }
    return color_map.get(industry, "#000000")
