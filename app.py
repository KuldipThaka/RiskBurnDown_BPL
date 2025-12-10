import streamlit as st
from utils.auth import init_auth, login_page, logout
from utils.data import load_data
from components.add_risk import render_add_risk
from components.dashboard import render_dashboard

st.set_page_config(page_title="BPL Risk Management", layout="wide")
init_auth()

if not st.session_state.get('logged_in', False):
    login_page()

user_type = st.session_state.get('user_type')
if user_type is None:
    user_type = "User"

st.sidebar.title(f"👋 Welcome, {user_type.title()} Manager")
page = st.sidebar.selectbox("Select Page", ["➕ Add Risk", "📉 Risk Burndown Dashboard"])
st.sidebar.button("🚪 Logout", on_click=logout)

df = load_data()
page = st.sidebar.selectbox(
    "Select Page",
    ["Dashboard", "Add Risk"]   # you can change order if you want
)

if page == "Add Risk":
    render_add_risk(df)
else:
    render_dashboard(df)