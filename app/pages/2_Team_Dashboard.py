"""
Team Dashboard Page for the Trading Simulation Web App.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.auth import is_authenticated, is_admin, get_current_team_id, get_current_team_name, get_current_team_industry
from app.database import get_session
from app.models import Team, Inventory, Transaction, TradeRequest
from app.services.production_service import produce_material_units, get_production_requirements, get_production_history
from app.services.excel_service import export_team_data
from app.utils.constants import INDUSTRIES
from app.utils.helpers import format_currency, get_industry_emoji

st.set_page_config(page_title="Dashboard - Trading Simulation", page_icon="📊", layout="wide")

# Check authentication
if not is_authenticated():
    st.error("⚠️ Please log in to access this page.")
    st.stop()

if is_admin():
    st.warning("👑 Admins should use the Admin Panel instead.")
    st.stop()

team_id = get_current_team_id()
team_name = get_current_team_name()
team_industry = get_current_team_industry()

st.title(f"📊 {team_name} Dashboard")
st.markdown(f"**Industry:** {get_industry_emoji(team_industry)} {team_industry}")

# Fetch team data
with get_session() as session:
    team = session.query(Team).filter(Team.id == team_id).first()
    inventories = session.query(Inventory).filter(Inventory.team_id == team_id).order_by(Inventory.industry).all()
    
    # Get recent transactions
    recent_transactions = session.query(Transaction).filter(
        (Transaction.from_team_id == team_id) | (Transaction.to_team_id == team_id)
    ).order_by(Transaction.created_at.desc()).limit(10).all()
    
    # Get recent trade requests
    recent_trades = session.query(TradeRequest).filter(
        (TradeRequest.from_team_id == team_id) | (TradeRequest.to_team_id == team_id)
    ).order_by(TradeRequest.created_at.desc()).limit(5).all()

st.divider()

# Balance Card
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 1rem; color: white; text-align: center;">
        <h4 style="margin: 0; color: white;">💰 Current Balance</h4>
        <h2 style="margin: 0.5rem 0; color: white;">{format_currency(team.current_balance)}</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 1.5rem; border-radius: 1rem; color: white; text-align: center;">
        <h4 style="margin: 0; color: white;">📈 Initial Balance</h4>
        <h2 style="margin: 0.5rem 0; color: white;">{format_currency(team.initial_balance)}</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    pnl = team.current_balance - team.initial_balance
    pnl_color = "28a745" if pnl >= 0 else "dc3545"
    pnl_sign = "+" if pnl >= 0 else ""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #{pnl_color} 0%, #{pnl_color}aa 100%); padding: 1.5rem; border-radius: 1rem; color: white; text-align: center;">
        <h4 style="margin: 0; color: white;">📊 P&L</h4>
        <h2 style="margin: 0.5rem 0; color: white;">{pnl_sign}{format_currency(pnl)}</h2>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["📦 Inventory", "🏭 Production", "📜 Activity", "📥 Export"])

with tab1:
    st.subheader("📦 Inventory Overview")
    
    if inventories:
        cols = st.columns(5)
        for i, industry in enumerate(INDUSTRIES):
            inv = next((x for x in inventories if x.industry == industry), None)
            with cols[i]:
                is_own = industry == team_industry
                border_color = "#1f77b4" if is_own else "#e0e0e0"
                bg_color = "#e3f2fd" if is_own else "#f8f9fa"
                
                raw = inv.raw_units if inv else 0
                mat = inv.material_units if inv else 0
                
                with st.container(border=True):
                    st.markdown(f"**{get_industry_emoji(industry)} {industry}**")
                    if is_own:
                        st.caption("(Your Industry)")
                    st.divider()
                    st.markdown(f"**Raw Units:** {raw}")
                    st.markdown(f"**Material Units:** {mat}")
    else:
        st.info("No inventory data available. Admin needs to allocate initial resources.")

with tab2:
    st.subheader("🏭 Production")
    
    st.markdown(f"""
    **Production Rules:**
    - To produce **N** material units of **{team_industry}**:
    - You need **N raw units** from each of the other 4 industries
    - Raw units will be consumed, material units will be created
    """)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Produce Material Units")
        
        with st.form("production_form"):
            units_to_produce = st.number_input(
                "Units to Produce",
                min_value=1,
                max_value=1000,
                value=1,
                step=1,
                help="Enter the number of material units to produce"
            )
            
            # Show requirements
            req = get_production_requirements(team_id, units_to_produce)
            
            if req["success"]:
                st.markdown("**Requirements:**")
                for r in req["requirements"]:
                    status = "✅" if r["sufficient"] else "❌"
                    st.markdown(f"- {status} {r['industry']}: Need {r['required']}, Have {r['available']}")
            
            submit = st.form_submit_button("🏭 Produce", use_container_width=True)
            
            if submit:
                result = produce_material_units(team_id, units_to_produce)
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["error"])
    
    with col2:
        st.markdown("#### Production History")
        history = get_production_history(team_id, 5)
        
        if history:
            for log in history:
                with st.expander(f"Produced {log['units_produced']} units - {log['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                    st.markdown(f"""
                    - Cement used: {log['cement_used']}
                    - Energy used: {log['energy_used']}
                    - Iron used: {log['iron_used']}
                    - Aluminium used: {log['aluminium_used']}
                    - Wood used: {log['wood_used']}
                    """)
        else:
            st.info("No production history yet.")

with tab3:
    st.subheader("📜 Recent Activity")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Recent Transactions")
        if recent_transactions:
            for tx in recent_transactions:
                with get_session() as session:
                    from_team = session.query(Team).filter(Team.id == tx.from_team_id).first() if tx.from_team_id else None
                    to_team = session.query(Team).filter(Team.id == tx.to_team_id).first() if tx.to_team_id else None
                
                direction = "📤" if tx.from_team_id == team_id else "📥"
                st.markdown(f"""
                {direction} **{tx.type.replace('_', ' ').title()}** - {format_currency(tx.amount)}
                <br><small>{tx.description or 'No description'}</small>
                <br><small style="color: gray;">{tx.created_at.strftime('%Y-%m-%d %H:%M')}</small>
                """, unsafe_allow_html=True)
                st.divider()
        else:
            st.info("No transactions yet.")
    
    with col2:
        st.markdown("#### Recent Trade Requests")
        if recent_trades:
            for trade in recent_trades:
                with get_session() as session:
                    from_team = session.query(Team).filter(Team.id == trade.from_team_id).first()
                    to_team = session.query(Team).filter(Team.id == trade.to_team_id).first()
                
                direction = "Sent to" if trade.from_team_id == team_id else "Received from"
                other_team = to_team.name if trade.from_team_id == team_id else from_team.name
                
                status_emoji = {"pending": "⏳", "accepted": "✅", "rejected": "❌", "cancelled": "🚫"}
                
                st.markdown(f"""
                {status_emoji.get(trade.status, '❓')} **{direction} {other_team}**
                <br>{trade.units_requested} {trade.industry} units @ {format_currency(trade.offered_price_per_unit)}/unit
                <br><small style="color: gray;">Status: {trade.status.title()} | {trade.created_at.strftime('%Y-%m-%d %H:%M')}</small>
                """, unsafe_allow_html=True)
                st.divider()
        else:
            st.info("No trade requests yet.")

with tab4:
    st.subheader("📥 Export My Data")
    
    st.markdown("Download your team's data as an Excel file.")
    
    if st.button("📥 Download My Data as Excel", use_container_width=True):
        excel_data = export_team_data(team_id)
        st.download_button(
            label="📄 Click to Download",
            data=excel_data,
            file_name=f"{team_name.replace(' ', '_')}_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
