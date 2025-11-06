from components.dashboard import render_dashboard_page
from utils.data import load_data

df = load_data()
render_dashboard_page(df)