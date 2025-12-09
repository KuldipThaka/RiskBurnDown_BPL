from components.add_risk import render_add_risk
from utils.data import load_data

df = load_data()
render_add_risk(df)