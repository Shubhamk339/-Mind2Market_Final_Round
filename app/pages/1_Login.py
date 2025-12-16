"""
Login Page for the Trading Simulation Web App.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.auth import login_user, is_authenticated


st.title("🔐 Login")

if is_authenticated():
    st.success(f"✅ You are already logged in as **{st.session_state.get('team_name', 'User')}**")
    st.info("Use the sidebar to navigate to other pages.")
    
    if st.button("Go to Home"):
        st.switch_page("main.py")
else:
    st.markdown("""
    Enter your team credentials to access the trading simulation.
    
    ---
    """)
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            submit = st.form_submit_button("🔓 Login", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                result = login_user(username, password)
                
                if result["success"]:
                    st.session_state["authenticated"] = True
                    st.session_state["team_id"] = result["team_id"]
                    st.session_state["team_name"] = result["team_name"]
                    st.session_state["industry"] = result["industry"]
                    st.session_state["is_admin"] = result["is_admin"]
                    st.session_state["is_super_admin"] = result.get("is_super_admin", False)
                    
                    st.success(f"✅ Welcome, {result['team_name']}!")
                    st.rerun()
                else:
                    st.error(f"❌ {result['error']}")
    
    st.divider()
    
    with st.expander("ℹ️ Need Help?"):
        st.markdown("""
        **For Company Teams:**
        - Username: `companyname` (e.g., `tatasteel`, `relianceenergy`)
        - Password: `companynameyearofestablishment` (e.g., `tatasteel1907`)
        
        **For GameMaster (Administrator):**
        - Username: `gamemaster`
        - Password: `gamemaster369`
        """)
