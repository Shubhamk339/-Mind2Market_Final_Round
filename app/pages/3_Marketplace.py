"""
Marketplace Page for the Trading Simulation Web App.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.auth import is_authenticated, is_admin, get_current_team_id, get_current_team_name, get_current_team_industry
from app.database import get_session
from app.models import Team, Inventory, MarketplaceOffer
from app.services.trading_service import (
    create_marketplace_offer, update_marketplace_offer, buy_from_marketplace,
    get_active_offers, get_team_offers
)
from app.utils.constants import INDUSTRIES
from app.utils.helpers import format_currency, get_industry_emoji

st.set_page_config(page_title="Marketplace - Trading Simulation", page_icon="🏪", layout="wide")

# Check authentication
if not is_authenticated():
    st.error("⚠️ Please log in to access this page.")
    st.stop()

if is_admin():
    st.warning("👑 Admins should use the Admin Panel to monitor marketplace.")
    st.stop()

team_id = get_current_team_id()
team_name = get_current_team_name()
team_industry = get_current_team_industry()

st.title("🏪 Marketplace")
st.markdown(f"**Your Industry:** {get_industry_emoji(team_industry)} {team_industry} | **Balance:** {format_currency(0)}")

# Refresh balance
with get_session() as session:
    team = session.query(Team).filter(Team.id == team_id).first()
    current_balance = team.current_balance if team else 0

st.markdown(f"**Balance:** {format_currency(current_balance)}")

st.divider()

# Tabs
tab1, tab2, tab3 = st.tabs(["🛒 Browse Offers", "📤 My Sell Offers", "➕ Create Offer"])

with tab1:
    st.subheader("🛒 Available Offers")
    
    # Filters
    col1, col2 = st.columns([1, 3])
    with col1:
        industry_filter = st.selectbox(
            "Filter by Industry",
            ["All"] + INDUSTRIES,
            key="market_filter"
        )
    
    # Get offers
    filter_industry = None if industry_filter == "All" else industry_filter
    offers = get_active_offers(industry_filter=filter_industry, exclude_team_id=team_id)
    
    if offers:
        st.markdown(f"**{len(offers)} offers available**")
        
        for offer in offers:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1.5, 2.5])
                
                with col1:
                    st.markdown(f"""
                    **{get_industry_emoji(offer['industry'])} {offer['industry']}**
                    <br><small>Seller: {offer['seller_name']}</small>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.metric("Units", offer['units_available'])
                
                with col3:
                    st.metric("Price/Unit", format_currency(offer['price_per_unit']))
                
                with col4:
                    with st.form(f"buy_form_{offer['id']}"):
                        max_units = min(offer['units_available'], int(current_balance / offer['price_per_unit']))
                        units_to_buy = st.number_input(
                            "Units",
                            min_value=1,
                            max_value=max(1, max_units),
                            value=1,
                            key=f"units_{offer['id']}"
                        )
                        total_cost = units_to_buy * offer['price_per_unit']
                        st.caption(f"Total: {format_currency(total_cost)}")
                        
                        if st.form_submit_button("🛒 Buy", use_container_width=True):
                            result = buy_from_marketplace(team_id, offer['id'], units_to_buy)
                            if result['success']:
                                st.success(result['message'])
                                st.rerun()
                            else:
                                st.error(result['error'])
                
                st.divider()
    else:
        st.info("No offers available at the moment. Check back later!")

with tab2:
    st.subheader("📤 My Sell Offers")
    
    my_offers = get_team_offers(team_id)
    
    if my_offers:
        for offer in my_offers:
            status_badge = "🟢 Active" if offer['is_active'] else "🔴 Inactive"
            
            with st.expander(f"{get_industry_emoji(offer['industry'])} {offer['units_available']} units @ {format_currency(offer['price_per_unit'])}/unit - {status_badge}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"**Created:** {offer['created_at'].strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    new_price = st.number_input(
                        "New Price",
                        min_value=0.01,
                        value=float(offer['price_per_unit']),
                        step=0.01,
                        key=f"price_{offer['id']}"
                    )
                    if st.button("Update Price", key=f"update_{offer['id']}"):
                        result = update_marketplace_offer(offer['id'], team_id, new_price=new_price)
                        if result['success']:
                            st.success(result['message'])
                            st.rerun()
                        else:
                            st.error(result['error'])
                
                with col3:
                    if offer['is_active']:
                        if st.button("🚫 Deactivate", key=f"deactivate_{offer['id']}"):
                            result = update_marketplace_offer(offer['id'], team_id, deactivate=True)
                            if result['success']:
                                st.success("Offer deactivated")
                                st.rerun()
                            else:
                                st.error(result['error'])
    else:
        st.info("You haven't created any sell offers yet.")

with tab3:
    st.subheader("➕ Create New Sell Offer")
    
    st.markdown(f"""
    **Note:** You can only sell **{team_industry}** material units (your own industry).
    """)
    
    # Get available material units
    with get_session() as session:
        inventory = session.query(Inventory).filter(
            Inventory.team_id == team_id,
            Inventory.industry == team_industry
        ).first()
        
        available_units = inventory.material_units if inventory else 0
    
    st.info(f"Available {team_industry} material units: **{available_units}**")
    
    if available_units > 0:
        with st.form("create_offer_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                units_to_sell = st.number_input(
                    "Units to Sell",
                    min_value=1,
                    max_value=available_units,
                    value=min(10, available_units),
                    step=1
                )
            
            with col2:
                price_per_unit = st.number_input(
                    "Price per Unit (₹)",
                    min_value=0.01,
                    value=100.00,
                    step=0.01
                )
            
            total_value = units_to_sell * price_per_unit
            st.markdown(f"**Total Listing Value:** {format_currency(total_value)}")
            
            if st.form_submit_button("📤 Create Offer", use_container_width=True):
                result = create_marketplace_offer(team_id, units_to_sell, price_per_unit)
                if result['success']:
                    st.success(result['message'])
                    st.rerun()
                else:
                    st.error(result['error'])
    else:
        st.warning("You don't have any material units to sell. Produce some first!")
