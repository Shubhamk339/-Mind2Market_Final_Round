"""
Admin Reports Page for the Trading Simulation Web App.
"""

import streamlit as st
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.auth import is_authenticated, is_admin
from app.database import get_session
from app.models import Team
from app.services.excel_service import export_full_snapshot, export_team_data
from app.services.trading_service import get_leaderboard_data
from app.utils.helpers import format_currency, get_industry_emoji

st.set_page_config(page_title="Admin Reports - Trading Simulation", page_icon="📋", layout="wide")

# Check authentication and admin privileges
if not is_authenticated():
    st.error("⚠️ Please log in to access this page.")
    st.stop()

if not is_admin():
    st.error("⚠️ This page is for administrators only.")
    st.stop()

st.title("📋 Admin Reports")

st.divider()

# Tabs
tab1, tab2, tab3 = st.tabs(["📥 Export Data", "📊 Quick Stats", "🏆 Leaderboard Snapshot"])

with tab1:
    st.subheader("📥 Export Game Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Full Game Snapshot")
        st.markdown("""
        Export all game data including:
        - Teams
        - Inventory
        - Marketplace Offers
        - Trade Requests
        - Transactions
        - Production Logs
        - Gifts
        - Leaderboard
        """)
        
        if st.button("📥 Download Full Snapshot", use_container_width=True, type="primary"):
            excel_data = export_full_snapshot()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📄 Click to Download Excel File",
                data=excel_data,
                file_name=f"trading_simulation_snapshot_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col2:
        st.markdown("### Export by Team")
        st.markdown("Download data for a specific team.")
        
        with get_session() as session:
            teams = session.query(Team).filter(Team.is_admin == False).order_by(Team.name).all()
            team_options = {f"{t.name} ({t.industry})": t.id for t in teams}
        
        if team_options:
            selected_team = st.selectbox("Select Team", list(team_options.keys()))
            
            if st.button("📥 Download Team Data", use_container_width=True):
                team_id = team_options[selected_team]
                excel_data = export_team_data(team_id)
                team_name = selected_team.split(" (")[0].replace(" ", "_")
                st.download_button(
                    label="📄 Click to Download",
                    data=excel_data,
                    file_name=f"{team_name}_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.info("No teams available to export.")

with tab2:
    st.subheader("📊 Quick Statistics")
    
    with get_session() as session:
        from app.models import Transaction, MarketplaceOffer, TradeRequest, ProductionLog, Gift
        from sqlalchemy import func
        
        # Team stats
        team_count = session.query(Team).filter(Team.is_admin == False).count()
        total_balance = session.query(func.sum(Team.current_balance)).filter(Team.is_admin == False).scalar() or 0
        
        # Transaction stats
        total_transactions = session.query(Transaction).count()
        total_transaction_value = session.query(func.sum(Transaction.amount)).scalar() or 0
        
        # Marketplace stats
        active_offers = session.query(MarketplaceOffer).filter(MarketplaceOffer.is_active == True).count()
        total_offers = session.query(MarketplaceOffer).count()
        
        # Trade request stats
        pending_trades = session.query(TradeRequest).filter(TradeRequest.status == "pending").count()
        accepted_trades = session.query(TradeRequest).filter(TradeRequest.status == "accepted").count()
        
        # Production stats
        total_production = session.query(func.sum(ProductionLog.units_produced)).scalar() or 0
        
        # Gift stats
        gifts_sent = session.query(Gift).filter(Gift.is_applied == True).count()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 👥 Teams")
        st.metric("Total Teams", team_count)
        st.metric("Total Balance", format_currency(total_balance))
    
    with col2:
        st.markdown("### 💰 Transactions")
        st.metric("Total Transactions", total_transactions)
        st.metric("Total Value", format_currency(total_transaction_value))
    
    with col3:
        st.markdown("### 🏪 Marketplace")
        st.metric("Active Offers", active_offers)
        st.metric("Total Offers", total_offers)
    
    with col4:
        st.markdown("### 🔄 Activity")
        st.metric("Pending Trades", pending_trades)
        st.metric("Accepted Trades", accepted_trades)
        st.metric("Total Production", f"{total_production} units")
        st.metric("Gifts Sent", f"{gifts_sent} / {team_count}")
    
    st.divider()
    
    # Industry breakdown
    st.markdown("### 📈 Industry Breakdown")
    
    from app.utils.constants import INDUSTRIES
    
    industry_cols = st.columns(5)
    
    for i, industry in enumerate(INDUSTRIES):
        with industry_cols[i]:
            with get_session() as session:
                industry_teams = session.query(Team).filter(
                    Team.industry == industry,
                    Team.is_admin == False
                ).count()
                
                from app.models import Inventory
                total_raw = session.query(func.sum(Inventory.raw_units)).filter(
                    Inventory.industry == industry
                ).scalar() or 0
                
                total_material = session.query(func.sum(Inventory.material_units)).filter(
                    Inventory.industry == industry
                ).scalar() or 0
            
            st.markdown(f"#### {get_industry_emoji(industry)} {industry}")
            st.metric("Teams", industry_teams)
            st.metric("Raw Units", total_raw)
            st.metric("Material Units", total_material)

with tab3:
    st.subheader("🏆 Current Leaderboard")
    
    leaderboard = get_leaderboard_data()
    
    if leaderboard:
        # Display as table
        st.markdown("### Rankings")
        
        header_cols = st.columns([0.5, 2, 1.5, 1.5, 1.5, 1.5, 1.5])
        headers = ["#", "Team", "Revenue", "Profit", "Production", "Purchases", "Balance"]
        for col, header in zip(header_cols, headers):
            col.markdown(f"**{header}**")
        
        st.divider()
        
        for team in leaderboard:
            row_cols = st.columns([0.5, 2, 1.5, 1.5, 1.5, 1.5, 1.5])
            
            rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(team['rank'], "")
            
            row_cols[0].markdown(f"{rank_emoji} {team['rank']}")
            row_cols[1].markdown(f"{get_industry_emoji(team['industry'])} {team['team_name']}")
            row_cols[2].markdown(format_currency(team['revenue']))
            
            profit_color = "green" if team['profit'] >= 0 else "red"
            row_cols[3].markdown(f"<span style='color:{profit_color}'>{format_currency(team['profit'])}</span>", unsafe_allow_html=True)
            
            row_cols[4].markdown(f"{team['total_production']}")
            row_cols[5].markdown(f"{team['total_purchases']}")
            row_cols[6].markdown(format_currency(team['current_balance']))
        
        st.divider()
        
        # Summary statistics
        st.markdown("### Summary")
        
        total_revenue = sum(t['revenue'] for t in leaderboard)
        total_profit = sum(t['profit'] for t in leaderboard)
        total_prod = sum(t['total_production'] for t in leaderboard)
        
        summary_cols = st.columns(4)
        summary_cols[0].metric("Total Revenue", format_currency(total_revenue))
        summary_cols[1].metric("Total Profit", format_currency(total_profit))
        summary_cols[2].metric("Total Production", f"{total_prod} units")
        summary_cols[3].metric("Avg Balance", format_currency(sum(t['current_balance'] for t in leaderboard) / len(leaderboard)))
    else:
        st.info("No teams registered yet.")
