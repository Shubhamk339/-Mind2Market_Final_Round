"""
Gift service for admin gift operations.
"""

from datetime import datetime
from ..database import get_session
from ..models import Team, Inventory, Gift, Transaction
from ..utils.constants import TransactionType


def can_receive_gift(team_id: int) -> dict:
    """
    Check if a team can receive a gift (only 1 gift per team allowed).
    """
    with get_session() as session:
        team = session.query(Team).filter(Team.id == team_id).first()
        if not team:
            return {"can_receive": False, "error": "Team not found"}
        
        if team.is_admin:
            return {"can_receive": False, "error": "Admin cannot receive gifts"}
        
        existing_gift = session.query(Gift).filter(
            Gift.team_id == team_id,
            Gift.is_applied == True
        ).first()
        
        if existing_gift:
            return {"can_receive": False, "error": "Team has already received a gift"}
        
        return {"can_receive": True, "team_industry": team.industry}


def send_gift(admin_id: int, team_id: int, material_units: int) -> dict:
    """
    Send a gift of material units from admin to a team.
    
    Rules:
    - Only admin can send gifts
    - Only one gift per team
    - Gift contains only material_units (for team's own industry)
    - No money gifts
    """
    if material_units <= 0:
        return {"success": False, "error": "Material units must be positive"}
    
    with get_session() as session:
        admin = session.query(Team).filter(Team.id == admin_id, Team.is_admin == True).first()
        if not admin:
            return {"success": False, "error": "Admin not found or unauthorized"}
        
        team = session.query(Team).filter(Team.id == team_id, Team.is_admin == False).first()
        if not team:
            return {"success": False, "error": "Team not found"}
        
        # Check if team already received a gift
        existing_gift = session.query(Gift).filter(
            Gift.team_id == team_id,
            Gift.is_applied == True
        ).first()
        
        if existing_gift:
            return {"success": False, "error": "Team has already received a gift"}
        
        # Get or create inventory for team's own industry
        inventory = session.query(Inventory).filter(
            Inventory.team_id == team_id,
            Inventory.industry == team.industry
        ).first()
        
        if not inventory:
            inventory = Inventory(
                team_id=team_id,
                industry=team.industry,
                raw_units=0,
                material_units=0
            )
            session.add(inventory)
        
        # Add material units to inventory
        inventory.material_units += material_units
        inventory.last_updated = datetime.utcnow()
        
        # Create gift record
        gift = Gift(
            team_id=team_id,
            industry=team.industry,
            material_units_gifted=material_units,
            sent_by_admin_id=admin_id,
            is_applied=True
        )
        session.add(gift)
        
        # Log transaction
        transaction = Transaction(
            type=TransactionType.GIFT,
            from_team_id=None,  # Admin (system)
            to_team_id=team_id,
            industry=team.industry,
            units=material_units,
            amount=0,  # No money in gift
            description=f"Admin gift: {material_units} {team.industry} material units"
        )
        session.add(transaction)
        
        return {
            "success": True,
            "message": f"Successfully sent {material_units} {team.industry} material units to {team.name}"
        }


def get_gift_status(team_id: int) -> dict:
    """
    Get gift status for a team.
    """
    with get_session() as session:
        team = session.query(Team).filter(Team.id == team_id).first()
        if not team:
            return {"success": False, "error": "Team not found"}
        
        gift = session.query(Gift).filter(
            Gift.team_id == team_id,
            Gift.is_applied == True
        ).first()
        
        if gift:
            return {
                "success": True,
                "has_gift": True,
                "gift": {
                    "industry": gift.industry,
                    "units": gift.material_units_gifted,
                    "received_at": gift.created_at
                }
            }
        
        return {"success": True, "has_gift": False}


def get_all_gifts() -> list:
    """
    Get all gifts sent (for admin view).
    """
    with get_session() as session:
        gifts = session.query(Gift).order_by(Gift.created_at.desc()).all()
        
        result = []
        for gift in gifts:
            team = session.query(Team).filter(Team.id == gift.team_id).first()
            result.append({
                "id": gift.id,
                "team_id": gift.team_id,
                "team_name": team.name if team else "Unknown",
                "industry": gift.industry,
                "units": gift.material_units_gifted,
                "is_applied": gift.is_applied,
                "created_at": gift.created_at
            })
        
        return result


def get_teams_without_gifts() -> list:
    """
    Get list of teams that haven't received a gift yet.
    """
    with get_session() as session:
        # Get teams that are not admin
        teams = session.query(Team).filter(Team.is_admin == False).all()
        
        # Get teams that have received gifts
        gifted_team_ids = session.query(Gift.team_id).filter(Gift.is_applied == True).all()
        gifted_team_ids = {t[0] for t in gifted_team_ids}
        
        result = []
        for team in teams:
            if team.id not in gifted_team_ids:
                result.append({
                    "id": team.id,
                    "name": team.name,
                    "industry": team.industry
                })
        
        return result
