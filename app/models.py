"""
SQLAlchemy ORM models for the trading simulation application.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .database import Base
from .utils.constants import INDUSTRIES, GAME_STATUSES, TRANSACTION_TYPES, TRADE_STATUSES


class Team(Base):
    """Team model representing participating teams."""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    industry = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    initial_balance = Column(Float, default=250000)
    current_balance = Column(Float, default=250000)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    inventory = relationship("Inventory", back_populates="team", cascade="all, delete-orphan")
    marketplace_offers = relationship("MarketplaceOffer", back_populates="seller", cascade="all, delete-orphan")
    production_logs = relationship("ProductionLog", back_populates="team", cascade="all, delete-orphan")
    gifts_received = relationship("Gift", back_populates="team", foreign_keys="Gift.team_id", cascade="all, delete-orphan")


class Inventory(Base):
    """Inventory model tracking raw and material units for each team per industry."""
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    industry = Column(String(50), nullable=False)
    raw_units = Column(Integer, default=0)
    material_units = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="inventory")


class MarketplaceOffer(Base):
    """Marketplace offers for selling material units."""
    __tablename__ = "marketplace_offers"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    industry = Column(String(50), nullable=False)
    material_units_available = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    seller = relationship("Team", back_populates="marketplace_offers")


class TradeRequest(Base):
    """Trade requests for bilateral team-to-team trades."""
    __tablename__ = "trade_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    from_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    to_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    industry = Column(String(50), nullable=False)
    units_requested = Column(Integer, nullable=False)
    offered_price_per_unit = Column(Float, nullable=False)
    total_offer_amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending")
    is_secret_deal = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    from_team = relationship("Team", foreign_keys=[from_team_id])
    to_team = relationship("Team", foreign_keys=[to_team_id])


class Transaction(Base):
    """Transaction log for all money and unit movements."""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)
    from_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    to_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    industry = Column(String(50), nullable=True)
    units = Column(Integer, nullable=True)
    amount = Column(Float, nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    from_team = relationship("Team", foreign_keys=[from_team_id])
    to_team = relationship("Team", foreign_keys=[to_team_id])


class ProductionLog(Base):
    """Log of material unit production."""
    __tablename__ = "production_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    units_produced = Column(Integer, nullable=False)
    input_cement_units_used = Column(Integer, default=0)
    input_energy_units_used = Column(Integer, default=0)
    input_iron_units_used = Column(Integer, default=0)
    input_aluminium_units_used = Column(Integer, default=0)
    input_wood_units_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="production_logs")


class Gift(Base):
    """Admin gifts to teams."""
    __tablename__ = "gifts"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    industry = Column(String(50), nullable=False)
    material_units_gifted = Column(Integer, nullable=False)
    sent_by_admin_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    is_applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", foreign_keys=[team_id], back_populates="gifts_received")
    admin = relationship("Team", foreign_keys=[sent_by_admin_id])


class GameState(Base):
    """Game state tracking."""
    __tablename__ = "game_state"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(20), default="not_started")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
