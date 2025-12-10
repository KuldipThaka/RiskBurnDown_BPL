 
import pandas as pd
import streamlit as st

def filter_by_user_type(df):
    user_type = st.session_state.get('user_type', 'business')  # safe default
    if user_type == 'tech':
        return df[df['Risk Type'] == 'Technical'].copy()
    return df.copy()