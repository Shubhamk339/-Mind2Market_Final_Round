"""
Leaderboard Page for the Trading Simulation Web App.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

from app.auth import is_authenticated
from app.services.trading_service import get_leaderboard_data
from app.utils.constants import AUTO_REFRESH_INTERVAL
from app.utils.helpers import format_currency, get_industry_emoji

st.set_page_config(page_title="Leaderboard - Trading Simulation", page_icon="🏆", layout="wide")

st.title("🏆 Leaderboard")

# Auto-refresh for real-time feel
if HAS_AUTOREFRESH:
    count = st_autorefresh(interval=AUTO_REFRESH_INTERVAL, limit=None, key="leaderboard_refresh")
    st.caption(f"🔄 Auto-refreshing every {AUTO_REFRESH_INTERVAL // 1000} seconds")
else:
    st.caption("💡 Refresh the page to see latest standings")
    if st.button("🔄 Refresh"):
        st.rerun()

st.divider()

# Get leaderboard data
leaderboard = get_leaderboard_data()

if leaderboard:
    # Top 3 podium
    if len(leaderboard) >= 3:
        st.subheader("🥇🥈🥉 Top 3 Teams")
        
        cols = st.columns([1, 1.2, 1])
        
        # Second place
        with cols[0]:
            team = leaderboard[1]
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #C0C0C0 0%, #A0A0A0 100%); padding: 1.5rem; border-radius: 1rem; text-align: center; color: white; margin-top: 2rem;">
                <h2 style="color: white;">🥈</h2>
                <h3 style="color: white; margin: 0;">{team['team_name']}</h3>
                <p style="margin: 0.5rem 0;">{get_industry_emoji(team['industry'])} {team['industry']}</p>
                <h4 style="color: white;">Revenue: {format_currency(team['revenue'])}</h4>
            </div>
            """, unsafe_allow_html=True)
        
        # First place
        with cols[1]:
            team = leaderboard[0]
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); padding: 2rem; border-radius: 1rem; text-align: center; color: white;">
                <h1 style="color: white;">🥇</h1>
                <h2 style="color: white; margin: 0;">{team['team_name']}</h2>
                <p style="margin: 0.5rem 0;">{get_industry_emoji(team['industry'])} {team['industry']}</p>
                <h3 style="color: white;">Revenue: {format_currency(team['revenue'])}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        # Third place
        with cols[2]:
            team = leaderboard[2]
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #CD7F32 0%, #8B4513 100%); padding: 1.5rem; border-radius: 1rem; text-align: center; color: white; margin-top: 2rem;">
                <h2 style="color: white;">🥉</h2>
                <h3 style="color: white; margin: 0;">{team['team_name']}</h3>
                <p style="margin: 0.5rem 0;">{get_industry_emoji(team['industry'])} {team['industry']}</p>
                <h4 style="color: white;">Revenue: {format_currency(team['revenue'])}</h4>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
    
    # Full leaderboard table
    st.subheader("📊 Full Standings")
    
    # Create table header
    header_cols = st.columns([0.5, 2, 1.5, 1.5, 1.5, 1.5, 1.5])
    with header_cols[0]:
        st.markdown("**Rank**")
    with header_cols[1]:
        st.markdown("**Team**")
    with header_cols[2]:
        st.markdown("**Revenue**")
    with header_cols[3]:
        st.markdown("**Profit**")
    with header_cols[4]:
        st.markdown("**Production**")
    with header_cols[5]:
        st.markdown("**Purchases**")
    with header_cols[6]:
        st.markdown("**Balance**")
    
    st.divider()
    
    # Table rows
    for team in leaderboard:
        rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(team['rank'], "")
        
        row_cols = st.columns([0.5, 2, 1.5, 1.5, 1.5, 1.5, 1.5])
        
        with row_cols[0]:
            st.markdown(f"**{rank_emoji} {team['rank']}**")
        
        with row_cols[1]:
            st.markdown(f"{get_industry_emoji(team['industry'])} {team['team_name']}")
        
        with row_cols[2]:
            st.markdown(f"{format_currency(team['revenue'])}")
        
        with row_cols[3]:
            profit_color = "green" if team['profit'] >= 0 else "red"
            st.markdown(f"<span style='color: {profit_color};'>{format_currency(team['profit'])}</span>", unsafe_allow_html=True)
        
        with row_cols[4]:
            st.markdown(f"{team['total_production']} units")
        
        with row_cols[5]:
            st.markdown(f"{team['total_purchases']} units")
        
        with row_cols[6]:
            st.markdown(f"{format_currency(team['current_balance'])}")
        
        st.divider()
    
    # Statistics summary
    st.subheader("📈 Game Statistics")
    
    total_revenue = sum(t['revenue'] for t in leaderboard)
    total_production = sum(t['total_production'] for t in leaderboard)
    total_purchases = sum(t['total_purchases'] for t in leaderboard)
    avg_balance = sum(t['current_balance'] for t in leaderboard) / len(leaderboard) if leaderboard else 0
    
    stat_cols = st.columns(4)
    
    with stat_cols[0]:
        st.metric("Total Revenue", format_currency(total_revenue))
    
    with stat_cols[1]:
        st.metric("Total Production", f"{total_production} units")
    
    with stat_cols[2]:
        st.metric("Total Purchases", f"{total_purchases} units")
    
    with stat_cols[3]:
        st.metric("Avg Balance", format_currency(avg_balance))

else:
    st.info("No teams registered yet. The leaderboard will appear once teams are created.")
    
    st.markdown("""
    ### Leaderboard Ranking Criteria
    
    Teams are ranked by:
    1. **Revenue** (highest priority)
    2. **Profit** (in case of tie)
    3. **Total Production** (second tiebreaker)
    4. **Total Purchases** (third tiebreaker)
    """)
