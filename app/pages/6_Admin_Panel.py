"""
Admin Panel Page for the Trading Simulation Web App.
"""

import streamlit as st
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.auth import is_authenticated, is_admin, get_current_team_id, hash_password
from app.database import get_session
from app.models import Team, Inventory, GameState, Transaction, TradeRequest, MarketplaceOffer
from app.services.gift_service import send_gift, get_teams_without_gifts, get_all_gifts
from app.utils.constants import (
    INDUSTRIES, TEAMS_PER_INDUSTRY, INITIAL_BALANCE, GameStatus,
    MIN_INITIAL_RAW_UNITS, MAX_INITIAL_RAW_UNITS, TransactionType, COMPANY_TEAMS
)
from app.utils.helpers import format_currency, get_industry_emoji

st.set_page_config(page_title="Admin Panel - Trading Simulation", page_icon="👑", layout="wide")

# Check authentication and admin privileges
if not is_authenticated():
    st.error("⚠️ Please log in to access this page.")
    st.stop()

if not is_admin():
    st.error("⚠️ This page is for administrators only.")
    st.stop()

admin_id = get_current_team_id()

st.title("👑 Admin Panel")

# Game Status Control
with get_session() as session:
    game_state = session.query(GameState).first()
    current_status = game_state.status if game_state else GameStatus.NOT_STARTED

st.markdown(f"**Current Game Status:** {current_status.replace('_', ' ').title()}")

st.divider()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎮 Game Control",
    "👥 Team Setup",
    "🎁 Gifts",
    "🔍 Supervise Trades",
    "⚙️ Adjustments"
])

with tab1:
    st.subheader("🎮 Game Control")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Change Game Status")
        
        new_status = st.selectbox(
            "Select New Status",
            options=[GameStatus.NOT_STARTED, GameStatus.RUNNING, GameStatus.PAUSED, GameStatus.ENDED],
            index=[GameStatus.NOT_STARTED, GameStatus.RUNNING, GameStatus.PAUSED, GameStatus.ENDED].index(current_status)
        )
        
        if st.button("Update Game Status", use_container_width=True):
            with get_session() as session:
                game_state = session.query(GameState).first()
                if game_state:
                    game_state.status = new_status
                else:
                    game_state = GameState(status=new_status)
                    session.add(game_state)
            st.success(f"Game status updated to: {new_status.replace('_', ' ').title()}")
            st.rerun()
    
    with col2:
        st.markdown("### Game Statistics")
        
        with get_session() as session:
            team_count = session.query(Team).filter(Team.is_admin == False).count()
            total_transactions = session.query(Transaction).count()
            active_offers = session.query(MarketplaceOffer).filter(MarketplaceOffer.is_active == True).count()
            pending_trades = session.query(TradeRequest).filter(TradeRequest.status == "pending").count()
        
        st.metric("Total Teams", team_count)
        st.metric("Total Transactions", total_transactions)
        st.metric("Active Marketplace Offers", active_offers)
        st.metric("Pending Trade Requests", pending_trades)

with tab2:
    st.subheader("👥 Team Setup")
    
    # Check existing teams
    with get_session() as session:
        existing_teams = session.query(Team).filter(Team.is_admin == False).all()
    
    if existing_teams:
        st.success(f"✅ {len(existing_teams)} teams already exist.")
        
        with st.expander("View Existing Teams"):
            for team in existing_teams:
                st.markdown(f"- **{team.name}** ({get_industry_emoji(team.industry)} {team.industry}) - Balance: {format_currency(team.current_balance)}")
        
        st.warning("⚠️ Creating new teams will be added to existing teams.")
        
        # Delete All Teams Section
        st.markdown("---")
        st.markdown("### ⚠️ Danger Zone")
        
        col_del1, col_del2 = st.columns([3, 1])
        with col_del1:
            st.error("**Delete All Teams:** This will permanently remove all teams, their inventories, transactions, and trade data!")
        with col_del2:
            if st.button("🗑️ Delete All Teams", type="primary", use_container_width=True):
                st.session_state["confirm_delete_teams"] = True
        
        if st.session_state.get("confirm_delete_teams", False):
            st.warning("⚠️ Are you SURE you want to delete ALL teams? This action cannot be undone!")
            col_confirm1, col_confirm2 = st.columns(2)
            with col_confirm1:
                if st.button("✅ Yes, Delete All", type="primary", use_container_width=True):
                    with get_session() as session:
                        # Delete all related data first (due to foreign keys)
                        from app.models import Inventory, Transaction, TradeRequest, MarketplaceOffer, ProductionLog, Gift
                        session.query(Gift).delete()
                        session.query(ProductionLog).delete()
                        session.query(MarketplaceOffer).delete()
                        session.query(TradeRequest).delete()
                        session.query(Transaction).delete()
                        session.query(Inventory).delete()
                        session.query(Team).filter(Team.is_admin == False).delete()
                    st.session_state["confirm_delete_teams"] = False
                    st.success("✅ All teams deleted successfully!")
                    st.rerun()
            with col_confirm2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state["confirm_delete_teams"] = False
                    st.rerun()
    
    st.markdown("### Create Teams")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Auto-Generate 20 Company Teams")
        st.markdown("Creates 4 real company teams per industry with random raw unit allocation.")
        
        if st.button("🚀 Generate 20 Company Teams", use_container_width=True):
            with get_session() as session:
                created_count = 0
                for industry in INDUSTRIES:
                    companies = COMPANY_TEAMS.get(industry, [])
                    for company in companies:
                        # Check if team already exists
                        existing = session.query(Team).filter(Team.username == company["username"]).first()
                        if existing:
                            continue
                        
                        # Create team
                        team = Team(
                            name=company["name"],
                            industry=industry,
                            username=company["username"],
                            password_hash=hash_password(company["password"]),
                            initial_balance=INITIAL_BALANCE,
                            current_balance=INITIAL_BALANCE,
                            is_admin=False
                        )
                        session.add(team)
                        session.flush()  # Get team ID
                        
                        # Create inventory for all industries
                        for inv_industry in INDUSTRIES:
                            raw_units = random.randint(MIN_INITIAL_RAW_UNITS, MAX_INITIAL_RAW_UNITS)
                            inventory = Inventory(
                                team_id=team.id,
                                industry=inv_industry,
                                raw_units=raw_units,
                                material_units=0
                            )
                            session.add(inventory)
                        
                        created_count += 1
            
            if created_count > 0:
                st.success(f"✅ {created_count} company teams created successfully!")
                st.info("Password format: companynameyearofestablishment (e.g., ultratechcement1983)")
            else:
                st.warning("All company teams already exist!")
            st.rerun()
    
    with col2:
        st.markdown("#### Add Single Team")
        
        with st.form("add_team_form"):
            new_team_name = st.text_input("Team Name")
            new_team_industry = st.selectbox("Industry", INDUSTRIES)
            new_team_username = st.text_input("Username")
            new_team_password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Add Team"):
                if not all([new_team_name, new_team_username, new_team_password]):
                    st.error("Please fill all fields")
                else:
                    with get_session() as session:
                        existing = session.query(Team).filter(Team.username == new_team_username).first()
                        if existing:
                            st.error("Username already exists")
                        else:
                            team = Team(
                                name=new_team_name,
                                industry=new_team_industry,
                                username=new_team_username,
                                password_hash=hash_password(new_team_password),
                                initial_balance=INITIAL_BALANCE,
                                current_balance=INITIAL_BALANCE,
                                is_admin=False
                            )
                            session.add(team)
                            session.flush()
                            
                            for inv_industry in INDUSTRIES:
                                raw_units = random.randint(MIN_INITIAL_RAW_UNITS, MAX_INITIAL_RAW_UNITS)
                                inventory = Inventory(
                                    team_id=team.id,
                                    industry=inv_industry,
                                    raw_units=raw_units,
                                    material_units=0
                                )
                                session.add(inventory)
                            
                            st.success(f"Team '{new_team_name}' created!")
                            st.rerun()
    
    st.divider()
    
    st.markdown("### Reallocate Raw Units")
    st.warning("⚠️ This will reset all raw units for all teams!")
    
    col1, col2 = st.columns(2)
    with col1:
        min_units = st.number_input("Min Raw Units", min_value=1, value=MIN_INITIAL_RAW_UNITS)
    with col2:
        max_units = st.number_input("Max Raw Units", min_value=1, value=MAX_INITIAL_RAW_UNITS)
    
    if st.button("🔄 Reallocate All Raw Units"):
        with get_session() as session:
            teams = session.query(Team).filter(Team.is_admin == False).all()
            for team in teams:
                inventories = session.query(Inventory).filter(Inventory.team_id == team.id).all()
                for inv in inventories:
                    inv.raw_units = random.randint(min_units, max_units)
        st.success("Raw units reallocated!")
        st.rerun()

with tab3:
    st.subheader("🎁 Gift Management")
    
    st.markdown("""
    **Gift Rules:**
    - Each team can receive only ONE gift
    - Gifts contain material units only (no money)
    - Gifts are for the team's own industry
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Send Gift")
        
        teams_without_gifts = get_teams_without_gifts()
        
        if teams_without_gifts:
            with st.form("send_gift_form"):
                gift_team = st.selectbox(
                    "Select Team",
                    options=teams_without_gifts,
                    format_func=lambda x: f"{x['name']} ({get_industry_emoji(x['industry'])} {x['industry']})"
                )
                
                gift_units = st.number_input(
                    "Material Units to Gift",
                    min_value=1,
                    max_value=100,
                    value=10
                )
                
                if st.form_submit_button("🎁 Send Gift", use_container_width=True):
                    result = send_gift(admin_id, gift_team['id'], gift_units)
                    if result['success']:
                        st.success(result['message'])
                        st.rerun()
                    else:
                        st.error(result['error'])
        else:
            st.info("All teams have already received their gift!")
    
    with col2:
        st.markdown("### Gifts Sent")
        
        all_gifts = get_all_gifts()
        
        if all_gifts:
            for gift in all_gifts:
                st.markdown(f"""
                - **{gift['team_name']}**: {gift['units']} {get_industry_emoji(gift['industry'])} {gift['industry']} units
                <br><small>{gift['created_at'].strftime('%Y-%m-%d %H:%M')}</small>
                """, unsafe_allow_html=True)
        else:
            st.info("No gifts sent yet.")

with tab4:
    st.subheader("🔍 Supervise Trades")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_type = st.selectbox("Filter Type", ["All", "Marketplace", "Trade Requests", "Secret Deals"])
    
    with col2:
        with get_session() as session:
            all_teams = session.query(Team).filter(Team.is_admin == False).all()
            team_options = ["All Teams"] + [t.name for t in all_teams]
        filter_team = st.selectbox("Filter by Team", team_options)
    
    # Show transactions
    st.markdown("### Recent Transactions")
    
    with get_session() as session:
        query = session.query(Transaction).order_by(Transaction.created_at.desc())
        
        if filter_type == "Secret Deals":
            query = query.filter(Transaction.type == TransactionType.SECRET_TRADE)
        elif filter_type == "Marketplace":
            query = query.filter(Transaction.type.in_([TransactionType.PURCHASE, TransactionType.SALE]))
        
        if filter_team != "All Teams":
            team = session.query(Team).filter(Team.name == filter_team).first()
            if team:
                query = query.filter(
                    (Transaction.from_team_id == team.id) | (Transaction.to_team_id == team.id)
                )
        
        transactions = query.limit(50).all()
        
        if transactions:
            for tx in transactions:
                from_team = session.query(Team).filter(Team.id == tx.from_team_id).first() if tx.from_team_id else None
                to_team = session.query(Team).filter(Team.id == tx.to_team_id).first() if tx.to_team_id else None
                
                secret_badge = "🔒" if tx.type == TransactionType.SECRET_TRADE else ""
                
                with st.expander(f"{tx.type.replace('_', ' ').title()} - {format_currency(tx.amount)} {secret_badge}"):
                    st.markdown(f"""
                    - **From:** {from_team.name if from_team else 'System'}
                    - **To:** {to_team.name if to_team else 'N/A'}
                    - **Industry:** {tx.industry or 'N/A'}
                    - **Units:** {tx.units or 0}
                    - **Amount:** {format_currency(tx.amount)}
                    - **Description:** {tx.description or 'N/A'}
                    - **Time:** {tx.created_at.strftime('%Y-%m-%d %H:%M:%S')}
                    """)
        else:
            st.info("No transactions found.")

with tab5:
    st.subheader("⚙️ Manual Adjustments")
    
    st.warning("⚠️ Use with caution! All adjustments are logged.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Balance Adjustment")
        
        with st.form("balance_adjustment_form"):
            with get_session() as session:
                teams = session.query(Team).filter(Team.is_admin == False).all()
                team_options = {t.name: t.id for t in teams}
            
            adj_team = st.selectbox("Select Team", list(team_options.keys()), key="bal_team")
            adj_amount = st.number_input("Amount (positive to add, negative to deduct)", value=0.0, step=100.0)
            adj_reason = st.text_area("Reason for Adjustment")
            
            if st.form_submit_button("Apply Balance Adjustment"):
                if not adj_reason:
                    st.error("Please provide a reason")
                else:
                    with get_session() as session:
                        team = session.query(Team).filter(Team.id == team_options[adj_team]).first()
                        if team:
                            team.current_balance += adj_amount
                            
                            # Log transaction
                            tx = Transaction(
                                type=TransactionType.ADJUSTMENT,
                                from_team_id=admin_id,
                                to_team_id=team.id,
                                amount=abs(adj_amount),
                                description=f"Admin adjustment: {adj_reason}"
                            )
                            session.add(tx)
                    
                    st.success(f"Balance adjusted by {format_currency(adj_amount)}")
                    st.rerun()
    
    with col2:
        st.markdown("### Inventory Adjustment")
        
        with st.form("inventory_adjustment_form"):
            inv_team = st.selectbox("Select Team", list(team_options.keys()), key="inv_team")
            inv_industry = st.selectbox("Industry", INDUSTRIES)
            inv_type = st.selectbox("Unit Type", ["Raw Units", "Material Units"])
            inv_amount = st.number_input("Amount (positive to add, negative to deduct)", value=0, step=1)
            inv_reason = st.text_area("Reason for Adjustment", key="inv_reason")
            
            if st.form_submit_button("Apply Inventory Adjustment"):
                if not inv_reason:
                    st.error("Please provide a reason")
                else:
                    with get_session() as session:
                        team_id = team_options[inv_team]
                        inventory = session.query(Inventory).filter(
                            Inventory.team_id == team_id,
                            Inventory.industry == inv_industry
                        ).first()
                        
                        if inventory:
                            if inv_type == "Raw Units":
                                inventory.raw_units += inv_amount
                            else:
                                inventory.material_units += inv_amount
                            
                            # Log transaction
                            tx = Transaction(
                                type=TransactionType.ADJUSTMENT,
                                from_team_id=admin_id,
                                to_team_id=team_id,
                                industry=inv_industry,
                                units=abs(inv_amount),
                                amount=0,
                                description=f"Admin {inv_type} adjustment: {inv_reason}"
                            )
                            session.add(tx)
                            
                            st.success(f"Inventory adjusted!")
                            st.rerun()
                        else:
                            st.error("Inventory not found")
