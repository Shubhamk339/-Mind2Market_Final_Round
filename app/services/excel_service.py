"""
Excel export service for generating reports and data exports.
"""

import io
from datetime import datetime
import pandas as pd
from ..database import get_session
from ..models import Team, Inventory, MarketplaceOffer, TradeRequest, Transaction, ProductionLog, Gift
from .trading_service import get_leaderboard_data


def export_full_snapshot() -> io.BytesIO:
    """
    Export all game data to an Excel file with multiple sheets.
    Returns a BytesIO object containing the Excel file.
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Teams
        teams_df = _get_teams_df()
        teams_df.to_excel(writer, sheet_name='Teams', index=False)
        
        # Sheet 2: Inventory
        inventory_df = _get_inventory_df()
        inventory_df.to_excel(writer, sheet_name='Inventory', index=False)
        
        # Sheet 3: Marketplace Offers
        offers_df = _get_offers_df()
        offers_df.to_excel(writer, sheet_name='Marketplace Offers', index=False)
        
        # Sheet 4: Trade Requests
        trades_df = _get_trade_requests_df()
        trades_df.to_excel(writer, sheet_name='Trade Requests', index=False)
        
        # Sheet 5: Transactions
        transactions_df = _get_transactions_df()
        transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
        
        # Sheet 6: Production Logs
        production_df = _get_production_logs_df()
        production_df.to_excel(writer, sheet_name='Production Logs', index=False)
        
        # Sheet 7: Gifts
        gifts_df = _get_gifts_df()
        gifts_df.to_excel(writer, sheet_name='Gifts', index=False)
        
        # Sheet 8: Leaderboard
        leaderboard_df = _get_leaderboard_df()
        leaderboard_df.to_excel(writer, sheet_name='Leaderboard', index=False)
    
    output.seek(0)
    return output


def export_team_data(team_id: int) -> io.BytesIO:
    """
    Export data for a specific team.
    Returns a BytesIO object containing the Excel file.
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Team Info
        team_df = _get_team_info_df(team_id)
        team_df.to_excel(writer, sheet_name='Team Info', index=False)
        
        # Inventory
        inventory_df = _get_team_inventory_df(team_id)
        inventory_df.to_excel(writer, sheet_name='Inventory', index=False)
        
        # Trades (sent and received)
        trades_df = _get_team_trades_df(team_id)
        trades_df.to_excel(writer, sheet_name='Trades', index=False)
        
        # Production Logs
        production_df = _get_team_production_df(team_id)
        production_df.to_excel(writer, sheet_name='Production Logs', index=False)
        
        # Transactions
        transactions_df = _get_team_transactions_df(team_id)
        transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
    
    output.seek(0)
    return output


def _get_teams_df() -> pd.DataFrame:
    """Get all teams as DataFrame."""
    with get_session() as session:
        teams = session.query(Team).filter(Team.is_admin == False).all()
        data = [{
            'ID': t.id,
            'Name': t.name,
            'Industry': t.industry,
            'Username': t.username,
            'Initial Balance': t.initial_balance,
            'Current Balance': t.current_balance,
            'Created At': t.created_at
        } for t in teams]
        return pd.DataFrame(data)


def _get_inventory_df() -> pd.DataFrame:
    """Get all inventory as DataFrame."""
    with get_session() as session:
        inventories = session.query(Inventory).all()
        data = []
        for inv in inventories:
            team = session.query(Team).filter(Team.id == inv.team_id).first()
            data.append({
                'Team': team.name if team else 'Unknown',
                'Industry': inv.industry,
                'Raw Units': inv.raw_units,
                'Material Units': inv.material_units,
                'Last Updated': inv.last_updated
            })
        return pd.DataFrame(data)


def _get_offers_df() -> pd.DataFrame:
    """Get all marketplace offers as DataFrame."""
    with get_session() as session:
        offers = session.query(MarketplaceOffer).all()
        data = []
        for o in offers:
            seller = session.query(Team).filter(Team.id == o.seller_team_id).first()
            data.append({
                'ID': o.id,
                'Seller': seller.name if seller else 'Unknown',
                'Industry': o.industry,
                'Units Available': o.material_units_available,
                'Price Per Unit': o.price_per_unit,
                'Is Active': o.is_active,
                'Created At': o.created_at,
                'Updated At': o.updated_at
            })
        return pd.DataFrame(data)


def _get_trade_requests_df() -> pd.DataFrame:
    """Get all trade requests as DataFrame."""
    with get_session() as session:
        trades = session.query(TradeRequest).all()
        data = []
        for t in trades:
            from_team = session.query(Team).filter(Team.id == t.from_team_id).first()
            to_team = session.query(Team).filter(Team.id == t.to_team_id).first()
            data.append({
                'ID': t.id,
                'From Team': from_team.name if from_team else 'Unknown',
                'To Team': to_team.name if to_team else 'Unknown',
                'Industry': t.industry,
                'Units Requested': t.units_requested,
                'Price Per Unit': t.offered_price_per_unit,
                'Total Amount': t.total_offer_amount,
                'Status': t.status,
                'Is Secret Deal': t.is_secret_deal,
                'Created At': t.created_at,
                'Updated At': t.updated_at
            })
        return pd.DataFrame(data)


def _get_transactions_df() -> pd.DataFrame:
    """Get all transactions as DataFrame."""
    with get_session() as session:
        transactions = session.query(Transaction).order_by(Transaction.created_at.desc()).all()
        data = []
        for tx in transactions:
            from_team = session.query(Team).filter(Team.id == tx.from_team_id).first() if tx.from_team_id else None
            to_team = session.query(Team).filter(Team.id == tx.to_team_id).first() if tx.to_team_id else None
            data.append({
                'ID': tx.id,
                'Type': tx.type,
                'From Team': from_team.name if from_team else 'Admin/System',
                'To Team': to_team.name if to_team else 'N/A',
                'Industry': tx.industry or 'N/A',
                'Units': tx.units or 0,
                'Amount': tx.amount,
                'Description': tx.description,
                'Created At': tx.created_at
            })
        return pd.DataFrame(data)


def _get_production_logs_df() -> pd.DataFrame:
    """Get all production logs as DataFrame."""
    with get_session() as session:
        logs = session.query(ProductionLog).order_by(ProductionLog.created_at.desc()).all()
        data = []
        for log in logs:
            team = session.query(Team).filter(Team.id == log.team_id).first()
            data.append({
                'Team': team.name if team else 'Unknown',
                'Units Produced': log.units_produced,
                'Cement Used': log.input_cement_units_used,
                'Energy Used': log.input_energy_units_used,
                'Iron Used': log.input_iron_units_used,
                'Aluminium Used': log.input_aluminium_units_used,
                'Wood Used': log.input_wood_units_used,
                'Created At': log.created_at
            })
        return pd.DataFrame(data)


def _get_gifts_df() -> pd.DataFrame:
    """Get all gifts as DataFrame."""
    with get_session() as session:
        gifts = session.query(Gift).all()
        data = []
        for g in gifts:
            team = session.query(Team).filter(Team.id == g.team_id).first()
            admin = session.query(Team).filter(Team.id == g.sent_by_admin_id).first()
            data.append({
                'Team': team.name if team else 'Unknown',
                'Industry': g.industry,
                'Material Units Gifted': g.material_units_gifted,
                'Sent By': admin.name if admin else 'Admin',
                'Is Applied': g.is_applied,
                'Created At': g.created_at
            })
        return pd.DataFrame(data)


def _get_leaderboard_df() -> pd.DataFrame:
    """Get leaderboard as DataFrame."""
    leaderboard = get_leaderboard_data()
    return pd.DataFrame(leaderboard)


def _get_team_info_df(team_id: int) -> pd.DataFrame:
    """Get specific team info as DataFrame."""
    with get_session() as session:
        team = session.query(Team).filter(Team.id == team_id).first()
        if not team:
            return pd.DataFrame()
        
        data = [{
            'ID': team.id,
            'Name': team.name,
            'Industry': team.industry,
            'Initial Balance': team.initial_balance,
            'Current Balance': team.current_balance,
            'Created At': team.created_at
        }]
        return pd.DataFrame(data)


def _get_team_inventory_df(team_id: int) -> pd.DataFrame:
    """Get specific team inventory as DataFrame."""
    with get_session() as session:
        inventories = session.query(Inventory).filter(Inventory.team_id == team_id).all()
        data = [{
            'Industry': inv.industry,
            'Raw Units': inv.raw_units,
            'Material Units': inv.material_units,
            'Last Updated': inv.last_updated
        } for inv in inventories]
        return pd.DataFrame(data)


def _get_team_trades_df(team_id: int) -> pd.DataFrame:
    """Get trades involving specific team as DataFrame."""
    with get_session() as session:
        trades = session.query(TradeRequest).filter(
            (TradeRequest.from_team_id == team_id) | (TradeRequest.to_team_id == team_id)
        ).order_by(TradeRequest.created_at.desc()).all()
        
        data = []
        for t in trades:
            from_team = session.query(Team).filter(Team.id == t.from_team_id).first()
            to_team = session.query(Team).filter(Team.id == t.to_team_id).first()
            direction = "Sent" if t.from_team_id == team_id else "Received"
            data.append({
                'Direction': direction,
                'Other Party': to_team.name if direction == "Sent" else from_team.name,
                'Industry': t.industry,
                'Units': t.units_requested,
                'Price Per Unit': t.offered_price_per_unit,
                'Total': t.total_offer_amount,
                'Status': t.status,
                'Created At': t.created_at
            })
        return pd.DataFrame(data)


def _get_team_production_df(team_id: int) -> pd.DataFrame:
    """Get production logs for specific team as DataFrame."""
    with get_session() as session:
        logs = session.query(ProductionLog).filter(
            ProductionLog.team_id == team_id
        ).order_by(ProductionLog.created_at.desc()).all()
        
        data = [{
            'Units Produced': log.units_produced,
            'Cement Used': log.input_cement_units_used,
            'Energy Used': log.input_energy_units_used,
            'Iron Used': log.input_iron_units_used,
            'Aluminium Used': log.input_aluminium_units_used,
            'Wood Used': log.input_wood_units_used,
            'Created At': log.created_at
        } for log in logs]
        return pd.DataFrame(data)


def _get_team_transactions_df(team_id: int) -> pd.DataFrame:
    """Get transactions involving specific team as DataFrame."""
    with get_session() as session:
        transactions = session.query(Transaction).filter(
            (Transaction.from_team_id == team_id) | (Transaction.to_team_id == team_id)
        ).order_by(Transaction.created_at.desc()).all()
        
        data = []
        for tx in transactions:
            from_team = session.query(Team).filter(Team.id == tx.from_team_id).first() if tx.from_team_id else None
            to_team = session.query(Team).filter(Team.id == tx.to_team_id).first() if tx.to_team_id else None
            data.append({
                'Type': tx.type,
                'From': from_team.name if from_team else 'Admin/System',
                'To': to_team.name if to_team else 'N/A',
                'Industry': tx.industry or 'N/A',
                'Units': tx.units or 0,
                'Amount': tx.amount,
                'Description': tx.description,
                'Created At': tx.created_at
            })
        return pd.DataFrame(data)
