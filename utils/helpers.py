 
import pandas as pd
import streamlit as st

def filter_by_user_type(df):
    if st.session_state.user_type == 'tech':
        return df[df['Risk Type'] == 'Technical'].copy()
    return df.copy()