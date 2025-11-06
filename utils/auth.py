import streamlit as st
from config.settings import USERS

def init_auth():
    defaults = {
        'logged_in': False,
        'user_type': 'User',
        'data_source': 'local',
        'uploaded_df': None,
        'username': 'Guest'
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def login_page():
    st.markdown("<style>[data-testid='stSidebar'] {display: none !important;}</style>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='text-align: center; padding: 4rem 2rem;'>
    """, unsafe_allow_html=True)
    
    st.title("🔐 BPL Risk Management System")
    st.markdown("***Please login to continue***")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.selectbox("**Select User**", options=list(USERS.keys()), index=0)
        password = st.text_input("**Password**", type="password")
        
        if st.button("✅ **LOGIN**", use_container_width=True, type="primary"):
            if username in USERS and USERS[username]['password'] == password:
                st.session_state['logged_in'] = True
                st.session_state['user_type'] = USERS[username]['type']
                st.session_state['username'] = username
                st.success(f"✅ **Welcome, {username}!**")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ **Invalid username or password!**")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()  