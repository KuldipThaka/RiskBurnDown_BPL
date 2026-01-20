# -----------------------------
# Import required libraries
# -----------------------------
import streamlit as st

# Authentication utilities:
# - init_auth(): initializes authentication-related session variables
# - login_page(): renders the login UI
# - logout(): clears session and logs the user out
from utils.auth import init_auth, login_page, logout

# Data utility:
# - load_data(): loads risk-related data (e.g., CSV / DB) into a DataFrame
from utils.data import load_data

# UI components:
# - render_add_risk(): page for adding new risks
# - render_dashboard(): page for visualizing risk burndown & analytics
from components.add_risk import render_add_risk
from components.dashboard import render_dashboard


# -----------------------------
# Streamlit page configuration
# -----------------------------
# Sets the browser tab title and uses full-width layout
st.set_page_config(
    page_title="BPL Risk Management",
    layout="wide"
)

# -----------------------------
# Initialize authentication
# -----------------------------
# This typically sets up session_state variables like:
# - logged_in
# - user_type
init_auth()

# -----------------------------
# Login gate (security check)
# -----------------------------
# If the user is not logged in, show login page
# and stop rendering the rest of the app
if not st.session_state.get('logged_in', False):
    login_page()
    # NOTE:
    # login_page() is expected to handle authentication
    # and update st.session_state['logged_in']


# -----------------------------
# Read user role / type
# -----------------------------
# Example values:
# - "admin"
# - "risk"
# - "user"
user_type = st.session_state.get('user_type')

# Fallback in case user_type is not set
if user_type is None:
    user_type = "User"


# -----------------------------
# Sidebar UI
# -----------------------------
# Personalized welcome message in the sidebar
st.sidebar.title(f"👋 Welcome, {user_type.title()} Manager")

# NOTE:
# ⚠️ There are TWO selectboxes in this file.
# The second one (below) overrides this selection.
# This one is effectively unused.
page = st.sidebar.selectbox(
    "Select Page",
    ["➕ Add Risk", "📉 Risk Burndown Dashboard"]
)

# Logout button in the sidebar
# on_click triggers logout() which should clear session state
st.sidebar.button("🚪 Logout", on_click=logout)


# -----------------------------
# Load application data
# -----------------------------
# Loads the risk data once and passes it to pages
# Typically returns a pandas DataFrame
df = load_data()


# -----------------------------
# Page navigation (ACTIVE)
# -----------------------------
# This selectbox actually controls the page rendering
# (it overrides the earlier selectbox)
page = st.sidebar.selectbox(
    "Select Page",
    ["Dashboard", "Add Risk"]  # Order can be changed if needed
)


# -----------------------------
# Page routing / rendering
# -----------------------------
# Based on user selection, render the corresponding page
if page == "Add Risk":
    # Render the "Add Risk" form/page
    render_add_risk(df)
else:
    # Render the risk burndown dashboard
    render_dashboard(df)
