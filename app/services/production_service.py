"""
Production service for material unit production operations.
"""

from datetime import datetime
from ..database import get_session
from ..models import Team, Inventory, ProductionLog, Transaction
from ..utils.constants import INDUSTRIES, TransactionType
from ..utils.helpers import get_other_industries


def produce_material_units(team_id: int, units_to_produce: int) -> dict:
    """
    Produce material units for a team.
    
    To produce N material units of team's own industry:
    - Requires N raw_units from each of the other 4 industries
    - Deducts raw_units from those 4 industries
    - Adds N material_units to team's own industry
    """
    if units_to_produce <= 0:
        return {"success": False, "error": "Units to produce must be positive"}
    
    with get_session() as session:
        team = session.query(Team).filter(Team.id == team_id).first()
        if not team:
            return {"success": False, "error": "Team not found"}
        
        team_industry = team.industry
        other_industries = get_other_industries(team_industry)
        
        # Check if team has enough raw_units from each other industry
        inventory_map = {}
        for industry in other_industries:
            inv = session.query(Inventory).filter(
                Inventory.team_id == team_id,
                Inventory.industry == industry
            ).first()
            
            if not inv:
                return {"success": False, "error": f"No inventory for {industry}"}
            
            if inv.raw_units < units_to_produce:
                return {
                    "success": False, 
                    "error": f"Insufficient raw units for {industry}. Have {inv.raw_units}, need {units_to_produce}"
                }
            
            inventory_map[industry] = inv
        
        # Get team's own industry inventory
        own_inventory = session.query(Inventory).filter(
            Inventory.team_id == team_id,
            Inventory.industry == team_industry
        ).first()
        
        if not own_inventory:
            own_inventory = Inventory(
                team_id=team_id,
                industry=team_industry,
                raw_units=0,
                material_units=0
            )
            session.add(own_inventory)
        
        # Deduct raw_units from each other industry
        input_units = {
            "Cement": 0,
            "Energy": 0,
            "Iron": 0,
            "Aluminium": 0,
            "Wood": 0
        }
        
        for industry, inv in inventory_map.items():
            inv.raw_units -= units_to_produce
            inv.last_updated = datetime.utcnow()
            input_units[industry] = units_to_produce
        
        # Add material_units to team's own industry
        own_inventory.material_units += units_to_produce
        own_inventory.last_updated = datetime.utcnow()
        
        # Log production
        production_log = ProductionLog(
            team_id=team_id,
            units_produced=units_to_produce,
            input_cement_units_used=input_units.get("Cement", 0),
            input_energy_units_used=input_units.get("Energy", 0),
            input_iron_units_used=input_units.get("Iron", 0),
            input_aluminium_units_used=input_units.get("Aluminium", 0),
            input_wood_units_used=input_units.get("Wood", 0)
        )
        session.add(production_log)
        
        return {
            "success": True,
            "message": f"Successfully produced {units_to_produce} {team_industry} material units",
            "details": {
                "industry": team_industry,
                "units_produced": units_to_produce,
                "inputs_used": {k: v for k, v in input_units.items() if v > 0}
            }
        }


def get_production_requirements(team_id: int, units_to_produce: int) -> dict:
    """
    Get the requirements and availability for producing material units.
    """
    with get_session() as session:
        team = session.query(Team).filter(Team.id == team_id).first()
        if not team:
            return {"success": False, "error": "Team not found"}
        
        team_industry = team.industry
        other_industries = get_other_industries(team_industry)
        
        requirements = []
        can_produce = True
        
        for industry in other_industries:
            inv = session.query(Inventory).filter(
                Inventory.team_id == team_id,
                Inventory.industry == industry
            ).first()
            
            available = inv.raw_units if inv else 0
            required = units_to_produce
            sufficient = available >= required
            
            if not sufficient:
                can_produce = False
            
            requirements.append({
                "industry": industry,
                "required": required,
                "available": available,
                "sufficient": sufficient
            })
        
        return {
            "success": True,
            "team_industry": team_industry,
            "can_produce": can_produce,
            "requirements": requirements
        }


def get_production_history(team_id: int, limit: int = 10) -> list:
    """
    Get production history for a team.
    """
    with get_session() as session:
        logs = session.query(ProductionLog).filter(
            ProductionLog.team_id == team_id
        ).order_by(ProductionLog.created_at.desc()).limit(limit).all()
        
        return [{
            "id": log.id,
            "units_produced": log.units_produced,
            "cement_used": log.input_cement_units_used,
            "energy_used": log.input_energy_units_used,
            "iron_used": log.input_iron_units_used,
            "aluminium_used": log.input_aluminium_units_used,
            "wood_used": log.input_wood_units_used,
            "created_at": log.created_at
        } for log in logs]
