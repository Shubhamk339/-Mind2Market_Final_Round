"""
Trade Requests Page for the Trading Simulation Web App.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.auth import is_authenticated, is_admin, get_current_team_id, get_current_team_name, get_current_team_industry
from app.database import get_session
from app.models import Team, Inventory
from app.services.trading_service import (
    create_trade_request, accept_trade_request, reject_trade_request, cancel_trade_request,
    get_incoming_trade_requests, get_outgoing_trade_requests
)
from app.utils.constants import INDUSTRIES
from app.utils.helpers import format_currency, get_industry_emoji

st.set_page_config(page_title="Trade Requests - Trading Simulation", page_icon="🤝", layout="wide")

# Check authentication
if not is_authenticated():
    st.error("⚠️ Please log in to access this page.")
    st.stop()

if is_admin():
    st.warning("👑 Admins should use the Admin Panel to monitor trades.")
    st.stop()

team_id = get_current_team_id()
team_name = get_current_team_name()
team_industry = get_current_team_industry()

st.title("🤝 Trade Requests")

# Get current balance
with get_session() as session:
    team = session.query(Team).filter(Team.id == team_id).first()
    current_balance = team.current_balance if team else 0

st.markdown(f"**Your Balance:** {format_currency(current_balance)}")

st.divider()

# Tabs
tab1, tab2, tab3 = st.tabs(["📥 Incoming Requests", "📤 Outgoing Requests", "➕ Send New Request"])

with tab1:
    st.subheader("📥 Incoming Trade Requests")
    
    incoming = get_incoming_trade_requests(team_id)
    
    if incoming:
        for req in incoming:
            secret_badge = " 🔒 Secret" if req['is_secret'] else ""
            
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 2])
                
                with col1:
                    st.markdown(f"""
                    **From:** {req['from_team_name']}{secret_badge}
                    <br>**Requesting:** {req['units']} {get_industry_emoji(req['industry'])} {req['industry']} units
                    <br>**Offer:** {format_currency(req['price_per_unit'])}/unit = **{format_currency(req['total_amount'])}** total
                    <br><small style="color: gray;">{req['created_at'].strftime('%Y-%m-%d %H:%M')}</small>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Check if you have enough inventory
                    with get_session() as session:
                        inv = session.query(Inventory).filter(
                            Inventory.team_id == team_id,
                            Inventory.industry == req['industry']
                        ).first()
                        available = inv.material_units if inv else 0
                    
                    can_accept = available >= req['units']
                    st.caption(f"Your {req['industry']}: {available} units")
                
                with col3:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Accept", key=f"accept_{req['id']}", disabled=not can_accept):
                            result = accept_trade_request(req['id'], team_id)
                            if result['success']:
                                st.success(result['message'])
                                st.rerun()
                            else:
                                st.error(result['error'])
                    with col_b:
                        if st.button("❌ Reject", key=f"reject_{req['id']}"):
                            result = reject_trade_request(req['id'], team_id)
                            if result['success']:
                                st.success(result['message'])
                                st.rerun()
                            else:
                                st.error(result['error'])
                
                st.divider()
    else:
        st.info("No incoming trade requests at the moment.")

with tab2:
    st.subheader("📤 Outgoing Trade Requests")
    
    outgoing = get_outgoing_trade_requests(team_id)
    
    if outgoing:
        for req in outgoing:
            status_emoji = {
                "pending": "⏳",
                "accepted": "✅",
                "rejected": "❌",
                "cancelled": "🚫"
            }
            secret_badge = " 🔒" if req['is_secret'] else ""
            
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"""
                    **To:** {req['to_team_name']}{secret_badge}
                    <br>**Requesting:** {req['units']} {get_industry_emoji(req['industry'])} {req['industry']} units
                    <br>**Offer:** {format_currency(req['price_per_unit'])}/unit = **{format_currency(req['total_amount'])}** total
                    <br><small style="color: gray;">{req['created_at'].strftime('%Y-%m-%d %H:%M')}</small>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"**Status:** {status_emoji.get(req['status'], '❓')} {req['status'].title()}")
                
                with col3:
                    if req['status'] == 'pending':
                        if st.button("🚫 Cancel", key=f"cancel_{req['id']}"):
                            result = cancel_trade_request(req['id'], team_id)
                            if result['success']:
                                st.success(result['message'])
                                st.rerun()
                            else:
                                st.error(result['error'])
                
                st.divider()
    else:
        st.info("You haven't sent any trade requests yet.")

with tab3:
    st.subheader("➕ Send New Trade Request")
    
    st.markdown("""
    **Request to buy material units from another team.**
    
    💡 Tips:
    - You're requesting to BUY units from another team
    - The target team must accept for the trade to complete
    - Secret deals are not shown publicly but still count for leaderboard
    """)
    
    # Get list of other teams
    with get_session() as session:
        other_teams = session.query(Team).filter(
            Team.id != team_id,
            Team.is_admin == False
        ).order_by(Team.name).all()
        
        team_options = {t.name: {"id": t.id, "industry": t.industry} for t in other_teams}
    
    if team_options:
        with st.form("trade_request_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                selected_team = st.selectbox(
                    "Select Team",
                    options=list(team_options.keys())
                )
                
                if selected_team:
                    target_team = team_options[selected_team]
                    st.info(f"Industry: {get_industry_emoji(target_team['industry'])} {target_team['industry']}")
            
            with col2:
                # Industry should be the target team's industry (for material units)
                selected_industry = st.selectbox(
                    "Industry (Material to Buy)",
                    options=INDUSTRIES,
                    index=INDUSTRIES.index(target_team['industry']) if selected_team else 0
                )
            
            col3, col4 = st.columns(2)
            
            with col3:
                units_requested = st.number_input(
                    "Units to Request",
                    min_value=1,
                    max_value=1000,
                    value=10,
                    step=1
                )
            
            with col4:
                price_per_unit = st.number_input(
                    "Offered Price per Unit (₹)",
                    min_value=0.01,
                    value=100.00,
                    step=0.01
                )
            
            total_amount = units_requested * price_per_unit
            st.markdown(f"**Total Offer Amount:** {format_currency(total_amount)}")
            
            if total_amount > current_balance:
                st.warning(f"⚠️ Insufficient balance. You need {format_currency(total_amount)} but have {format_currency(current_balance)}")
            
            is_secret = st.checkbox("🔒 Make this a secret deal", help="Secret deals are hidden from public view but still affect your balance and leaderboard")
            
            submit = st.form_submit_button("📤 Send Trade Request", use_container_width=True)
            
            if submit:
                if total_amount > current_balance:
                    st.error("Insufficient balance for this trade request.")
                else:
                    result = create_trade_request(
                        from_team_id=team_id,
                        to_team_id=target_team['id'],
                        industry=selected_industry,
                        units=units_requested,
                        price_per_unit=price_per_unit,
                        is_secret=is_secret
                    )
                    if result['success']:
                        st.success(result['message'])
                        st.rerun()
                    else:
                        st.error(result['error'])
    else:
        st.warning("No other teams available to trade with.")
