from components.dashboard import render_dashboard
from utils.data import load_data

df = load_data()
render_dashboard(df)