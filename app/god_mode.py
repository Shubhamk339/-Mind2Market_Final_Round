"""
God Mode (Super Admin) - Universal Control for Trading Simulation
"""

import streamlit as st
import pandas as pd
from sqlalchemy import text
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.auth import is_authenticated, is_super_admin
from app.database import get_session
from app.models import Team, Inventory, GameState, Transaction, TradeRequest, MarketplaceOffer, Gift, ProductionLog, Base
from app.utils.constants import INDUSTRIES, TransactionType
from app.utils.helpers import format_currency, get_industry_emoji

# Service imports for impersonation
from app.services.production_service import produce_material_units
from app.services.trading_service import create_marketplace_offer, buy_from_marketplace, create_trade_request, get_active_offers



# Access Control
if not is_authenticated() or not is_super_admin():
    st.error("⛔ ACCESS DENIED: You do not have the divine power to be here.")
    st.stop()

st.title("⚡ GOD MODE")
st.markdown("### *Unlimited Power. Absolute Control.*")
st.divider()

# Tabs for different divine powers
tab1, tab2, tab3, tab4 = st.tabs(["⚡ God Actions", "📜 Universal SQL Editor", "🧨 Nuclear Options", "💾 Data Inspector"])

with tab1:
    st.subheader("⚡ God Actions")
    st.info("Perform actions on behalf of ANY team or force changes directly.")
    
    action_type = st.radio("Select Action Type", 
                          ["🎭 Impersonator", "🧱 Resource Editor", "🏭 Production Forcer", "🤝 Trade Manipulator"],
                          horizontal=True)
    
    st.divider()

    # Shared Team Selector Helper
    def get_team_options():
        with get_session() as session:
            teams = session.query(Team).filter(Team.is_admin == False).all()
            return {f"{t.name} ({t.industry})": t.id for t in teams}

    team_options = get_team_options()
    
    if action_type == "🎭 Impersonator":
        st.markdown("#### 🎭 Act as a Team")
        
        selected_team_name = st.selectbox("Select Team to Impersonate", list(team_options.keys()))
        team_id = team_options[selected_team_name]
        
        # Impersonation Sub-tabs
        imp_tab1, imp_tab2, imp_tab3 = st.tabs(["Sell on Market", "Buy from Market", "Send Trade Request"])
        
        with imp_tab1:
            st.markdown("##### Create Sell Offer")
            with st.form("imp_sell_form"):
                units = st.number_input("Units", min_value=1, value=10)
                price = st.number_input("Price per Unit", min_value=1.0, value=100.0)
                if st.form_submit_button("Force Create Offer"):
                    result = create_marketplace_offer(team_id, units, price)
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["error"])
                        
        with imp_tab2:
            st.markdown("##### Buy from Market")
            offers = get_active_offers(exclude_team_id=team_id)
            if offers:
                offer_opts = {f"{o['seller_name']} - {o['industry']} ({o['units_available']} units @ {o['price_per_unit']})": o for o in offers}
                selected_offer_key = st.selectbox("Select Offer", list(offer_opts.keys()))
                selected_offer = offer_opts[selected_offer_key]
                
                with st.form("imp_buy_form"):
                    buy_units = st.number_input("Units to Buy", min_value=1, max_value=selected_offer['units_available'], value=1)
                    if st.form_submit_button("Force Buy"):
                        result = buy_from_marketplace(team_id, selected_offer['id'], buy_units)
                        if result['success']:
                            st.success(result['message'])
                        else:
                            st.error(result['error'])
            else:
                st.info("No active offers available to buy.")

        with imp_tab3:
            st.markdown("##### Send Trade Request")
            target_team_name = st.selectbox("Target Team", [t for t in team_options.keys() if t != selected_team_name])
            target_id = team_options[target_team_name]
            
            with st.form("imp_trade_form"):
                ind = st.selectbox("Industry", INDUSTRIES)
                t_units = st.number_input("Units", min_value=1, value=10)
                t_price = st.number_input("Price/Unit", min_value=1.0, value=100.0)
                if st.form_submit_button("Force Send Request"):
                    result = create_trade_request(team_id, target_id, ind, t_units, t_price)
                    if result['success']:
                        st.success(result['message'])
                    else:
                        st.error(result['error'])

    elif action_type == "🧱 Resource Editor":
        st.markdown("#### 🧱 Modify Resources")
        
        target_team_name = st.selectbox("Select Team", list(team_options.keys()))
        target_id = team_options[target_team_name]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Inventory Control")
            with st.form("res_inv_form"):
                ind = st.selectbox("Industry", INDUSTRIES)
                u_type = st.radio("Type", ["Raw Units", "Material Units"])
                mode = st.radio("Mode", ["Add/Subtract", "Set Exact Value"])
                amount = st.number_input("Amount", value=0)
                
                if st.form_submit_button("Update Inventory"):
                    with get_session() as session:
                        inv = session.query(Inventory).filter(Inventory.team_id == target_id, Inventory.industry == ind).first()
                        if not inv:
                            inv = Inventory(team_id=target_id, industry=ind, raw_units=0, material_units=0)
                            session.add(inv)
                        
                        field = "raw_units" if u_type == "Raw Units" else "material_units"
                        current_val = getattr(inv, field)
                        
                        if mode == "Set Exact Value":
                            new_val = max(0, amount)
                        else:
                            new_val = max(0, current_val + amount)
                        
                        setattr(inv, field, new_val)
                        inv.last_updated = datetime.utcnow()
                        
                        # Log it
                        tx = Transaction(
                            type=TransactionType.ADJUSTMENT,
                            from_team_id=session.query(Team).filter(Team.username=="bricks").first().id,
                            to_team_id=target_id,
                            industry=ind,
                            units=abs(amount) if mode == "Add/Subtract" else 0,
                            amount=0,
                            description=f"God Mode: {mode} {u_type} for {ind} -> {new_val}"
                        )
                        session.add(tx)
                        
                        st.success(f"Updated {ind} {u_type} to {new_val}")

        with col2:
            st.markdown("##### Balance Control")
            with st.form("res_bal_form"):
                b_mode = st.radio("Mode", ["Add/Subtract", "Set Exact Value"], key="b_mode")
                b_amount = st.number_input("Amount (₹)", value=0.0)
                
                if st.form_submit_button("Update Balance"):
                    with get_session() as session:
                        team = session.query(Team).filter(Team.id == target_id).first()
                        
                        if b_mode == "Set Exact Value":
                            team.current_balance = b_amount
                        else:
                            team.current_balance += b_amount
                        
                        st.success(f"Balance updated to {format_currency(team.current_balance)}")

    elif action_type == "🏭 Production Forcer":
        st.markdown("#### 🏭 Force Production")
        
        target_team_name = st.selectbox("Select Team", list(team_options.keys()))
        target_id = team_options[target_team_name]
        
        with st.form("force_prod_form"):
            p_units = st.number_input("Units to Produce", min_value=1, value=100)
            ignore_costs = st.checkbox("🔥 IGNORE Raw Material Costs (Free Production)", value=False)
            
            if st.form_submit_button("🚀 Force Produce"):
                if not ignore_costs:
                    # Use standard service
                    result = produce_material_units(target_id, p_units)
                    if result['success']:
                        st.success(result['message'])
                    else:
                        st.error(result['error'])
                else:
                    # Custom "God" production logic
                    with get_session() as session:
                        team = session.query(Team).filter(Team.id == target_id).first()
                        
                        # Get own inventory
                        own_inv = session.query(Inventory).filter(
                            Inventory.team_id == target_id,
                            Inventory.industry == team.industry
                        ).first()
                        
                        if not own_inv:
                            own_inv = Inventory(team_id=target_id, industry=team.industry, raw_units=0, material_units=0)
                            session.add(own_inv)
                        
                        own_inv.material_units += p_units
                        own_inv.last_updated = datetime.utcnow()
                        
                        # Log fake production
                        log = ProductionLog(
                            team_id=target_id,
                            units_produced=p_units,
                            input_cement_units_used=0,
                            input_energy_units_used=0,
                            input_iron_units_used=0,
                            input_aluminium_units_used=0,
                            input_wood_units_used=0
                        )
                        session.add(log)
                        st.success(f"⚡ DIVINE INTERVENTION: Produced {p_units} units of {team.industry} for free!")

    elif action_type == "🤝 Trade Manipulator":
        st.markdown("#### 🤝 Force Direct Trade")
        st.warning("Forcefully transfers inventory and money between teams.")
        
        col1, col2 = st.columns(2)
        with col1:
            seller_name = st.selectbox("Seller Team", list(team_options.keys()), key="f_seller")
        with col2:
            buyer_name = st.selectbox("Buyer Team", list(team_options.keys()), key="f_buyer")
            
        seller_id = team_options[seller_name]
        buyer_id = team_options[buyer_name]
        
        if seller_id == buyer_id:
            st.error("Seller and Buyer cannot be the same.")
        
        with st.form("force_trade_form"):
            t_ind = st.selectbox("Industry", INDUSTRIES)
            t_units = st.number_input("Units to Transfer", min_value=1, value=10)
            total_price = st.number_input("Total Payment Amount (₹)", min_value=0.0, value=0.0)
            
            if st.form_submit_button("⚡ Execute Forced Trade"):
                if seller_id == buyer_id:
                    st.error("Select different teams.")
                else:
                    with get_session() as session:
                        # Get inventories
                        s_inv = session.query(Inventory).filter(Inventory.team_id == seller_id, Inventory.industry == t_ind).first()
                        b_inv = session.query(Inventory).filter(Inventory.team_id == buyer_id, Inventory.industry == t_ind).first()
                        
                        # Ensure inventories exist
                        if not s_inv:
                            s_inv = Inventory(team_id=seller_id, industry=t_ind, raw_units=0, material_units=0)
                            session.add(s_inv)
                        if not b_inv:
                            b_inv = Inventory(team_id=buyer_id, industry=t_ind, raw_units=0, material_units=0)
                            session.add(b_inv)
                            
                        # Move units (even if negative)
                        s_inv.material_units -= t_units
                        b_inv.raw_units += t_units # Buyer gets them as raw units usually? Or material? 
                        # Context: In game, buying usually means getting RAW units for production unless it is same industry.
                        # Detailed logic: If I buy Cement, I use it as raw material usually.
                        # Let's assume standard purchase flow: Buyer gets Raw Units.
                        
                        # Move money
                        seller_team = session.query(Team).filter(Team.id == seller_id).first()
                        buyer_team = session.query(Team).filter(Team.id == buyer_id).first()
                        
                        buyer_team.current_balance -= total_price
                        seller_team.current_balance += total_price
                        
                        # Log
                        tx = Transaction(
                            type=TransactionType.SECRET_TRADE,
                            from_team_id=buyer_id,
                            to_team_id=seller_id,
                            industry=t_ind,
                            units=t_units,
                            amount=total_price,
                            description=f"GOD FORCED TRADE: {t_units} {t_ind}"
                        )
                        session.add(tx)
                        
                        st.success("Trade forced successfully!")


with tab2:
    st.subheader("📜 Run Any SQL Query")
    st.warning("⚠️ WARNING: Direct database manipulation. No undos.")
    
    query = st.text_area("SQL Query", height=150, placeholder="SELECT * FROM teams WHERE ...\nUPDATE inventory SET ...\nDELETE FROM ...")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("▶️ Execute Query", type="primary", use_container_width=True):
            if query:
                with get_session() as session:
                    try:
                        result = session.execute(text(query))
                        
                        # Handle SELECT queries
                        if query.strip().upper().startswith("SELECT"):
                            rows = result.fetchall()
                            if rows:
                                df = pd.DataFrame(rows)
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.info("Query returned no results.")
                        else:
                            # Handle INSERT/UPDATE/DELETE
                            session.commit()
                            st.success(f"Query executed successfully. Rows affected: {result.rowcount}")
                            st.balloons()
                            
                    except Exception as e:
                        st.error(f"Error executing query: {str(e)}")
            else:
                st.warning("Please enter a query.")

with tab3:
    st.subheader("🧨 Nuclear Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Nukes")
        if st.button("🗑️ TRUNCATE LOGS (Transactions)", use_container_width=True):
            with get_session() as session:
                session.query(Transaction).delete()
                session.query(ProductionLog).delete()
                st.success("All transaction and production history has been erased.")
        
        if st.button("💀 DELETE ALL TEAMS", type="primary", use_container_width=True):
             with get_session() as session:
                session.query(Gift).delete()
                session.query(ProductionLog).delete()
                session.query(MarketplaceOffer).delete()
                session.query(TradeRequest).delete()
                session.query(Transaction).delete()
                session.query(Inventory).delete()
                session.query(Team).filter(Team.is_admin == False).delete()
                st.success("The simulation has been reset. All teams are gone.")

    with col2:
        st.markdown("#### Economy Control")
        if st.button("💰 Set All Balances to ₹10M", use_container_width=True):
            with get_session() as session:
                session.query(Team).filter(Team.is_admin == False).update({Team.current_balance: 10000000})
                st.success("All teams are now rich.")
        
        if st.button("🛑 Reset All Balances to ₹0", type="primary", use_container_width=True):
            with get_session() as session:
                session.query(Team).filter(Team.is_admin == False).update({Team.current_balance: 0})
                st.warning("All teams are now broke.")

    with col3:
        st.markdown("#### Game State Force")
        status = st.selectbox("Force Game Status", ["running", "paused", "ended", "not_started"])
        if st.button("Force Update Status"):
             with get_session() as session:
                game_state = session.query(GameState).first()
                if not game_state:
                    game_state = GameState(status=status)
                    session.add(game_state)
                else:
                    game_state.status = status
                st.success(f"Game status forced to: {status}")

with tab4:
    st.subheader("💾 Data Inspector")
    
    table_map = {
        "Teams": Team,
        "Inventory": Inventory,
        "Transactions": Transaction,
        "TradeRequests": TradeRequest,
        "MarketplaceOffers": MarketplaceOffer,
        "Gifts": Gift,
        "ProductionLogs": ProductionLog,
        "GameState": GameState
    }
    
    selected_table = st.selectbox("Select Table", list(table_map.keys()))
    
    if st.button("Load Data"):
        with get_session() as session:
            model = table_map[selected_table]
            # Use pandas to read sql
            try:
                # Simple query to list all
                items = session.query(model).all()
                if items:
                    data = [item.__dict__ for item in items]
                    # cleanup sqlalchemy state
                    for d in data:
                        d.pop('_sa_instance_state', None)
                    st.dataframe(pd.DataFrame(data))
                else:
                    st.info("Table is empty.")
            except Exception as e:
                st.error(f"Error loading table: {e}")
