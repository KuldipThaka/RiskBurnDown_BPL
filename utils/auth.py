# ---------------------------------------
# Import required libraries
# ---------------------------------------
import streamlit as st

# USERS dictionary contains:
# {
#   "username": {
#       "password": "xxxx",
#       "type": "Admin/User"
#   }
# }
from config.settings import USERS


# ---------------------------------------
# Initialize authentication session state
# ---------------------------------------
def init_auth():
    """
    Initializes default authentication-related values
    in Streamlit session_state.

    This ensures that session variables exist
    even before login occurs.
    """

    # Default session values
    defaults = {
        'logged_in': False,     # User authentication status
        'user_type': 'User',   # Role of the user (Admin/User)
        'data_source': 'local',# Data source selection
        'uploaded_df': None,   # Placeholder for uploaded data
        'username': 'Guest'    # Logged-in username
    }

    # Set defaults only if key does not already exist
    # (prevents overwriting values after login)
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------
# Login Page UI & Authentication Logic
# ---------------------------------------
def login_page():
    """
    Renders the login page and authenticates the user.
    Sidebar is hidden to prevent navigation before login.
    """

    # Hide sidebar completely on login screen
    st.markdown(
        "<style>[data-testid='stSidebar'] {display: none !important;}</style>",
        unsafe_allow_html=True
    )
    
    # Centered container for login UI
    st.markdown("""
    <div style='text-align: center; padding: 4rem 2rem;'>
    """, unsafe_allow_html=True)
    
    # App title
    st.title("🔐 BPL Risk Management System")
    st.markdown("***Please login to continue***")
    
    # Create 3-column layout for centering the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    # Middle column contains the login form
    with col2:
        # Dropdown to select a predefined user
        username = st.selectbox(
            "**Select User**",
            options=list(USERS.keys()),
            index=0
        )

        # Password input field (masked)
        password = st.text_input(
            "**Password**",
            type="password"
        )
        
        # Login button
        if st.button(
            "✅ **LOGIN**",
            use_container_width=True,
            type="primary"
        ):
            # Validate credentials
            if username in USERS and USERS[username]['password'] == password:
                
                # Update session state on successful login
                st.session_state['logged_in'] = True
                st.session_state['user_type'] = USERS[username]['type']
                st.session_state['username'] = username

                # Success feedback
                st.success(f"✅ **Welcome, {username}!**")
                st.balloons()

                # Reload app so authenticated pages render
                st.rerun()
            else:
                # Error message on failed login
                st.error("❌ **Invalid username or password!**")
    
    # Close HTML wrapper
    st.markdown("</div>", unsafe_allow_html=True)

    # Stop further execution so main app does not load
    st.stop()


# ---------------------------------------
# Logout Logic
# ---------------------------------------
def logout():
    """
    Logs out the user by clearing all session state
    and reloading the app.
    """

    # Remove all keys from session_state
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    # Reload app to show login page again
    st.rerun()
