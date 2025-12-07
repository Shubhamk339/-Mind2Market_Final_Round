"""
Trading service for marketplace and trade request operations.
"""

from datetime import datetime
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from ..database import get_session
from ..models import Team, Inventory, MarketplaceOffer, TradeRequest, Transaction, ProductionLog
from ..utils.constants import TransactionType, TradeStatus


def create_marketplace_offer(team_id: int, units: int, price_per_unit: float) -> dict:
    """
    Create a new marketplace sell offer for the team's own industry.
    """
    with get_session() as session:
        team = session.query(Team).filter(Team.id == team_id).first()
        if not team:
            return {"success": False, "error": "Team not found"}
        
        # Get inventory for team's own industry
        inventory = session.query(Inventory).filter(
            Inventory.team_id == team_id,
            Inventory.industry == team.industry
        ).first()
        
        if not inventory or inventory.material_units < units:
            return {"success": False, "error": "Insufficient material units available"}
        
        if units <= 0:
            return {"success": False, "error": "Units must be positive"}
        
        if price_per_unit <= 0:
            return {"success": False, "error": "Price must be positive"}
        
        # Create offer
        offer = MarketplaceOffer(
            seller_team_id=team_id,
            industry=team.industry,
            material_units_available=units,
            price_per_unit=price_per_unit,
            is_active=True
        )
        session.add(offer)
        
        return {"success": True, "message": f"Offer created for {units} units at ₹{price_per_unit}/unit"}


def update_marketplace_offer(offer_id: int, team_id: int, new_price: float = None, new_units: int = None, deactivate: bool = False) -> dict:
    """
    Update an existing marketplace offer.
    """
    with get_session() as session:
        offer = session.query(MarketplaceOffer).filter(
            MarketplaceOffer.id == offer_id,
            MarketplaceOffer.seller_team_id == team_id
        ).first()
        
        if not offer:
            return {"success": False, "error": "Offer not found or unauthorized"}
        
        if deactivate:
            offer.is_active = False
            return {"success": True, "message": "Offer deactivated"}
        
        if new_price is not None:
            if new_price <= 0:
                return {"success": False, "error": "Price must be positive"}
            offer.price_per_unit = new_price
        
        if new_units is not None:
            team = session.query(Team).filter(Team.id == team_id).first()
            inventory = session.query(Inventory).filter(
                Inventory.team_id == team_id,
                Inventory.industry == team.industry
            ).first()
            
            if not inventory or inventory.material_units < new_units:
                return {"success": False, "error": "Insufficient material units"}
            
            offer.material_units_available = new_units
        
        offer.updated_at = datetime.utcnow()
        return {"success": True, "message": "Offer updated successfully"}


def buy_from_marketplace(buyer_team_id: int, offer_id: int, units_to_buy: int) -> dict:
    """
    Buy material units from a marketplace offer.
    """
    with get_session() as session:
        offer = session.query(MarketplaceOffer).filter(
            MarketplaceOffer.id == offer_id,
            MarketplaceOffer.is_active == True
        ).first()
        
        if not offer:
            return {"success": False, "error": "Offer not found or inactive"}
        
        if offer.seller_team_id == buyer_team_id:
            return {"success": False, "error": "Cannot buy from your own offer"}
        
        if units_to_buy <= 0:
            return {"success": False, "error": "Units must be positive"}
        
        if units_to_buy > offer.material_units_available:
            return {"success": False, "error": "Not enough units available"}
        
        total_cost = units_to_buy * offer.price_per_unit
        
        # Get buyer and seller
        buyer = session.query(Team).filter(Team.id == buyer_team_id).first()
        seller = session.query(Team).filter(Team.id == offer.seller_team_id).first()
        
        if buyer.current_balance < total_cost:
            return {"success": False, "error": "Insufficient balance"}
        
        # Get seller's inventory (for that industry)
        seller_inventory = session.query(Inventory).filter(
            Inventory.team_id == seller.id,
            Inventory.industry == offer.industry
        ).first()
        
        if not seller_inventory or seller_inventory.material_units < units_to_buy:
            return {"success": False, "error": "Seller has insufficient inventory"}
        
        # Get or create buyer's inventory for that industry
        buyer_inventory = session.query(Inventory).filter(
            Inventory.team_id == buyer_team_id,
            Inventory.industry == offer.industry
        ).first()
        
        if not buyer_inventory:
            buyer_inventory = Inventory(
                team_id=buyer_team_id,
                industry=offer.industry,
                raw_units=0,
                material_units=0
            )
            session.add(buyer_inventory)
        
        # Perform the trade
        buyer.current_balance -= total_cost
        seller.current_balance += total_cost
        seller_inventory.material_units -= units_to_buy
        buyer_inventory.material_units += units_to_buy
        offer.material_units_available -= units_to_buy
        
        if offer.material_units_available == 0:
            offer.is_active = False
        
        offer.updated_at = datetime.utcnow()
        
        # Log transaction for buyer (purchase)
        buyer_transaction = Transaction(
            type=TransactionType.PURCHASE,
            from_team_id=buyer_team_id,
            to_team_id=seller.id,
            industry=offer.industry,
            units=units_to_buy,
            amount=total_cost,
            description=f"Purchased {units_to_buy} {offer.industry} units at ₹{offer.price_per_unit}/unit"
        )
        session.add(buyer_transaction)
        
        # Log transaction for seller (sale)
        seller_transaction = Transaction(
            type=TransactionType.SALE,
            from_team_id=seller.id,
            to_team_id=buyer_team_id,
            industry=offer.industry,
            units=units_to_buy,
            amount=total_cost,
            description=f"Sold {units_to_buy} {offer.industry} units at ₹{offer.price_per_unit}/unit"
        )
        session.add(seller_transaction)
        
        return {"success": True, "message": f"Successfully purchased {units_to_buy} units for ₹{total_cost:,.2f}"}


def get_active_offers(industry_filter: str = None, exclude_team_id: int = None) -> list:
    """
    Get all active marketplace offers, optionally filtered by industry.
    """
    with get_session() as session:
        query = session.query(MarketplaceOffer).filter(MarketplaceOffer.is_active == True)
        
        if industry_filter:
            query = query.filter(MarketplaceOffer.industry == industry_filter)
        
        if exclude_team_id:
            query = query.filter(MarketplaceOffer.seller_team_id != exclude_team_id)
        
        offers = query.order_by(MarketplaceOffer.price_per_unit).all()
        
        result = []
        for offer in offers:
            seller = session.query(Team).filter(Team.id == offer.seller_team_id).first()
            result.append({
                "id": offer.id,
                "seller_team_id": offer.seller_team_id,
                "seller_name": seller.name if seller else "Unknown",
                "industry": offer.industry,
                "units_available": offer.material_units_available,
                "price_per_unit": offer.price_per_unit,
                "created_at": offer.created_at
            })
        
        return result


def get_team_offers(team_id: int) -> list:
    """
    Get all offers by a specific team.
    """
    with get_session() as session:
        offers = session.query(MarketplaceOffer).filter(
            MarketplaceOffer.seller_team_id == team_id
        ).order_by(desc(MarketplaceOffer.created_at)).all()
        
        return [{
            "id": o.id,
            "industry": o.industry,
            "units_available": o.material_units_available,
            "price_per_unit": o.price_per_unit,
            "is_active": o.is_active,
            "created_at": o.created_at
        } for o in offers]


def create_trade_request(from_team_id: int, to_team_id: int, industry: str, 
                         units: int, price_per_unit: float, is_secret: bool = False) -> dict:
    """
    Create a bilateral trade request.
    """
    with get_session() as session:
        if from_team_id == to_team_id:
            return {"success": False, "error": "Cannot create trade request to yourself"}
        
        from_team = session.query(Team).filter(Team.id == from_team_id).first()
        to_team = session.query(Team).filter(Team.id == to_team_id).first()
        
        if not from_team or not to_team:
            return {"success": False, "error": "Team not found"}
        
        if units <= 0:
            return {"success": False, "error": "Units must be positive"}
        
        if price_per_unit <= 0:
            return {"success": False, "error": "Price must be positive"}
        
        total_amount = units * price_per_unit
        
        # Check if buyer (from_team) has sufficient balance
        if from_team.current_balance < total_amount:
            return {"success": False, "error": "Insufficient balance for this trade"}
        
        trade_request = TradeRequest(
            from_team_id=from_team_id,
            to_team_id=to_team_id,
            industry=industry,
            units_requested=units,
            offered_price_per_unit=price_per_unit,
            total_offer_amount=total_amount,
            status=TradeStatus.PENDING,
            is_secret_deal=is_secret
        )
        session.add(trade_request)
        
        return {"success": True, "message": f"Trade request sent to {to_team.name}"}


def accept_trade_request(request_id: int, accepting_team_id: int) -> dict:
    """
    Accept a trade request.
    """
    with get_session() as session:
        trade = session.query(TradeRequest).filter(
            TradeRequest.id == request_id,
            TradeRequest.to_team_id == accepting_team_id,
            TradeRequest.status == TradeStatus.PENDING
        ).first()
        
        if not trade:
            return {"success": False, "error": "Trade request not found or already processed"}
        
        buyer = session.query(Team).filter(Team.id == trade.from_team_id).first()
        seller = session.query(Team).filter(Team.id == trade.to_team_id).first()
        
        # Re-check buyer balance
        if buyer.current_balance < trade.total_offer_amount:
            return {"success": False, "error": "Buyer has insufficient balance"}
        
        # Check seller inventory
        seller_inventory = session.query(Inventory).filter(
            Inventory.team_id == seller.id,
            Inventory.industry == trade.industry
        ).first()
        
        if not seller_inventory or seller_inventory.material_units < trade.units_requested:
            return {"success": False, "error": "Insufficient material units to fulfill trade"}
        
        # Get or create buyer inventory
        buyer_inventory = session.query(Inventory).filter(
            Inventory.team_id == buyer.id,
            Inventory.industry == trade.industry
        ).first()
        
        if not buyer_inventory:
            buyer_inventory = Inventory(
                team_id=buyer.id,
                industry=trade.industry,
                raw_units=0,
                material_units=0
            )
            session.add(buyer_inventory)
        
        # Execute trade
        buyer.current_balance -= trade.total_offer_amount
        seller.current_balance += trade.total_offer_amount
        seller_inventory.material_units -= trade.units_requested
        buyer_inventory.material_units += trade.units_requested
        
        trade.status = TradeStatus.ACCEPTED
        trade.updated_at = datetime.utcnow()
        
        # Log transaction
        tx_type = TransactionType.SECRET_TRADE if trade.is_secret_deal else TransactionType.PURCHASE
        
        transaction = Transaction(
            type=tx_type,
            from_team_id=buyer.id,
            to_team_id=seller.id,
            industry=trade.industry,
            units=trade.units_requested,
            amount=trade.total_offer_amount,
            description=f"Trade: {trade.units_requested} {trade.industry} units at ₹{trade.offered_price_per_unit}/unit"
        )
        session.add(transaction)
        
        return {"success": True, "message": "Trade accepted successfully"}


def reject_trade_request(request_id: int, rejecting_team_id: int) -> dict:
    """
    Reject a trade request.
    """
    with get_session() as session:
        trade = session.query(TradeRequest).filter(
            TradeRequest.id == request_id,
            TradeRequest.to_team_id == rejecting_team_id,
            TradeRequest.status == TradeStatus.PENDING
        ).first()
        
        if not trade:
            return {"success": False, "error": "Trade request not found or already processed"}
        
        trade.status = TradeStatus.REJECTED
        trade.updated_at = datetime.utcnow()
        
        return {"success": True, "message": "Trade request rejected"}


def cancel_trade_request(request_id: int, team_id: int) -> dict:
    """
    Cancel a pending trade request (by sender).
    """
    with get_session() as session:
        trade = session.query(TradeRequest).filter(
            TradeRequest.id == request_id,
            TradeRequest.from_team_id == team_id,
            TradeRequest.status == TradeStatus.PENDING
        ).first()
        
        if not trade:
            return {"success": False, "error": "Trade request not found or already processed"}
        
        trade.status = TradeStatus.CANCELLED
        trade.updated_at = datetime.utcnow()
        
        return {"success": True, "message": "Trade request cancelled"}


def get_incoming_trade_requests(team_id: int) -> list:
    """
    Get incoming trade requests for a team.
    """
    with get_session() as session:
        trades = session.query(TradeRequest).filter(
            TradeRequest.to_team_id == team_id,
            TradeRequest.status == TradeStatus.PENDING
        ).order_by(desc(TradeRequest.created_at)).all()
        
        result = []
        for t in trades:
            from_team = session.query(Team).filter(Team.id == t.from_team_id).first()
            result.append({
                "id": t.id,
                "from_team_id": t.from_team_id,
                "from_team_name": from_team.name if from_team else "Unknown",
                "industry": t.industry,
                "units": t.units_requested,
                "price_per_unit": t.offered_price_per_unit,
                "total_amount": t.total_offer_amount,
                "is_secret": t.is_secret_deal,
                "created_at": t.created_at
            })
        
        return result


def get_outgoing_trade_requests(team_id: int) -> list:
    """
    Get outgoing trade requests from a team.
    """
    with get_session() as session:
        trades = session.query(TradeRequest).filter(
            TradeRequest.from_team_id == team_id
        ).order_by(desc(TradeRequest.created_at)).all()
        
        result = []
        for t in trades:
            to_team = session.query(Team).filter(Team.id == t.to_team_id).first()
            result.append({
                "id": t.id,
                "to_team_id": t.to_team_id,
                "to_team_name": to_team.name if to_team else "Unknown",
                "industry": t.industry,
                "units": t.units_requested,
                "price_per_unit": t.offered_price_per_unit,
                "total_amount": t.total_offer_amount,
                "status": t.status,
                "is_secret": t.is_secret_deal,
                "created_at": t.created_at
            })
        
        return result


def get_leaderboard_data() -> list:
    """
    Calculate and return leaderboard data for all teams.
    """
    with get_session() as session:
        teams = session.query(Team).filter(Team.is_admin == False).all()
        
        leaderboard = []
        for team in teams:
            # Calculate revenue (money received from sales)
            # In marketplace: seller is to_team_id in PURCHASE transactions
            # In trade requests: seller is to_team_id in PURCHASE/SECRET_TRADE, and they receive money
            # SALE transactions: from_team is the seller who received money
            
            # Revenue from being the seller in marketplace purchases (to_team receives money)
            marketplace_revenue = session.query(func.sum(Transaction.amount)).filter(
                Transaction.to_team_id == team.id,
                Transaction.type == TransactionType.PURCHASE
            ).scalar() or 0
            
            # Revenue from SALE type transactions (seller is from_team, they received money)
            sale_revenue = session.query(func.sum(Transaction.amount)).filter(
                Transaction.from_team_id == team.id,
                Transaction.type == TransactionType.SALE
            ).scalar() or 0
            
            # Revenue from secret trades where team is seller (to_team_id)
            secret_revenue = session.query(func.sum(Transaction.amount)).filter(
                Transaction.to_team_id == team.id,
                Transaction.type == TransactionType.SECRET_TRADE
            ).scalar() or 0
            
            total_revenue = marketplace_revenue + sale_revenue + secret_revenue
            
            # Calculate expenses (money spent on purchases)
            # From marketplace: buyer is from_team_id in PURCHASE transactions  
            purchase_expenses = session.query(func.sum(Transaction.amount)).filter(
                Transaction.from_team_id == team.id,
                Transaction.type == TransactionType.PURCHASE
            ).scalar() or 0
            
            # From trade requests accepted: buyer is from_team_id in SECRET_TRADE
            secret_expenses = session.query(func.sum(Transaction.amount)).filter(
                Transaction.from_team_id == team.id,
                Transaction.type == TransactionType.SECRET_TRADE
            ).scalar() or 0
            
            expenses = purchase_expenses + secret_expenses
            
            # Calculate total production
            total_production = session.query(func.sum(ProductionLog.units_produced)).filter(
                ProductionLog.team_id == team.id
            ).scalar() or 0
            
            # Calculate total purchases (units)
            total_purchases = session.query(func.sum(Transaction.units)).filter(
                Transaction.from_team_id == team.id,
                Transaction.type.in_([TransactionType.PURCHASE, TransactionType.SECRET_TRADE])
            ).scalar() or 0
            
            leaderboard.append({
                "team_id": team.id,
                "team_name": team.name,
                "industry": team.industry,
                "revenue": total_revenue,
                "expenses": expenses,
                "profit": total_revenue - expenses,
                "total_production": total_production,
                "total_purchases": total_purchases,
                "current_balance": team.current_balance
            })
        
        # Sort: Revenue desc, Profit desc, Production desc, Purchases desc
        leaderboard.sort(key=lambda x: (
            -x["revenue"],
            -x["profit"],
            -x["total_production"],
            -x["total_purchases"]
        ))
        
        # Add rank
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1
        
        return leaderboard
