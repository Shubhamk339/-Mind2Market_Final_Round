"""
Main entry point for the Trading Simulation Web App.
"""

import streamlit as st
import sys
import os

# Add the app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, get_session
from app.models import Team, GameState
from app.auth import hash_password, is_authenticated, is_admin, get_current_team_name, get_current_team_industry, logout_user
from app.utils.constants import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_NAME, GameStatus

# Page configuration
st.set_page_config(
    page_title="Trading Simulation",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on startup
init_db()


def create_admin_if_not_exists():
    """Create default admin user if not exists."""
    with get_session() as session:
        admin = session.query(Team).filter(Team.username == DEFAULT_ADMIN_USERNAME).first()
        if not admin:
            admin = Team(
                name=DEFAULT_ADMIN_NAME,
                industry="Admin",
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                initial_balance=0,
                current_balance=0,
                is_admin=True
            )
            session.add(admin)
            
        # Create game state if not exists
        game_state = session.query(GameState).first()
        if not game_state:
            game_state = GameState(status=GameStatus.NOT_STARTED)
            session.add(game_state)


def get_game_status():
    """Get current game status."""
    with get_session() as session:
        game_state = session.query(GameState).first()
        return game_state.status if game_state else GameStatus.NOT_STARTED


# Create admin on startup
create_admin_if_not_exists()

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-badge {
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
        display: inline-block;
    }
    .status-running { background-color: #28a745; color: white; }
    .status-paused { background-color: #ffc107; color: black; }
    .status-ended { background-color: #dc3545; color: white; }
    .status-not-started { background-color: #6c757d; color: white; }
    .balance-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/bar-chart.png", width=80)
    st.title("📈 Trading Sim")
    
    # Game status
    game_status = get_game_status()
    status_colors = {
        GameStatus.NOT_STARTED: "🔵",
        GameStatus.RUNNING: "🟢",
        GameStatus.PAUSED: "🟡",
        GameStatus.ENDED: "🔴"
    }
    st.markdown(f"**Game Status:** {status_colors.get(game_status, '⚪')} {game_status.replace('_', ' ').title()}")
    
    st.divider()
    
    if is_authenticated():
        st.markdown(f"**Team:** {get_current_team_name()}")
        if not is_admin():
            st.markdown(f"**Industry:** {get_current_team_industry()}")
        
        st.divider()
        
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()
    else:
        st.info("Please log in to access the system.")

# Main content based on authentication
if not is_authenticated():
    st.markdown('<h1 class="main-header">🏭 Trading Simulation</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Welcome to the Multi-Team Trading Simulation!
    
    This is an interactive trading game where teams compete across 5 industries:
    - 🏗️ **Cement**
    - ⚡ **Energy**
    - 🔩 **Iron**
    - 🔧 **Aluminium**
    - 🪵 **Wood**
    
    #### How to Play:
    1. **Login** with your team credentials
    2. **Produce** material units using raw materials from other industries
    3. **Sell** your materials on the marketplace
    4. **Trade** with other teams directly
    5. **Climb** the leaderboard!
    
    ---
    
    👉 **Navigate to the Login page** using the sidebar to get started.
    """)
else:
    st.markdown('<h1 class="main-header">🏭 Trading Simulation Dashboard</h1>', unsafe_allow_html=True)
    
    if is_admin():
        st.success("👑 Welcome, Administrator! Use the sidebar to navigate to Admin pages.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 📊 Admin Panel")
            st.write("Manage teams, allocate resources, and control the game.")
        with col2:
            st.markdown("### 📋 Reports")
            st.write("Export game data and generate reports.")
        with col3:
            st.markdown("### 🏆 Leaderboard")
            st.write("View team rankings and performance.")
    else:
        # Show team dashboard summary
        from app.database import get_session
        from app.models import Team, Inventory
        
        team_id = st.session_state.get("team_id")
        
        with get_session() as session:
            team = session.query(Team).filter(Team.id == team_id).first()
            if team:
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown(f"""
                    <div class="balance-card">
                        <h3>Current Balance</h3>
                        <h1>₹{team.current_balance:,.2f}</h1>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("### Quick Stats")
                    inventories = session.query(Inventory).filter(Inventory.team_id == team_id).all()
                    
                    cols = st.columns(5)
                    for i, inv in enumerate(inventories):
                        with cols[i]:
                            is_own = inv.industry == team.industry
                            bg_color = "#e3f2fd" if is_own else "#f5f5f5"
                            st.markdown(f"""
                            <div style="background: {bg_color}; padding: 0.5rem; border-radius: 0.5rem; text-align: center;">
                                <small>{inv.industry}</small><br>
                                <b>Raw: {inv.raw_units}</b><br>
                                <b>Mat: {inv.material_units}</b>
                            </div>
                            """, unsafe_allow_html=True)
        
        st.divider()
        st.info("👉 Use the sidebar to navigate to Dashboard, Marketplace, Trade Requests, or Leaderboard.")
