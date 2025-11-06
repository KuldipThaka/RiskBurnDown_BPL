 
import pandas as pd
import streamlit as st
import os
from config.settings import EXCEL_FILE, ALL_STANDARD_COLUMNS

def validate_columns(df):
    required_mapping = {
        'Risk ID': ['Risk ID', 'risk_id', 'ID'],
        'Risk Description': ['Risk Description', 'Description'],
        'Risk Open Date': ['Risk Open Date', 'Open Date'],
        'Expected End Date (DD-MMM-YY)': ['Expected End Date'],
        'Closure Date (DD-MMM-YY)': ['Closure Date'],
        'Risk Type': ['Risk Type', 'Type'],
        'Probability': ['Probability'],
        'Impact': ['Impact'],
        'Difficulty': ['Difficulty'],
        'Priority': ['Priority'],
        'Action Plan': ['Action Plan'],
        'Owner': ['Owner']
    }
    
    column_mapping = {}
    missing = []
    
    for standard, possibles in required_mapping.items():
        found = False
        for col in df.columns:
            if any(p.lower() in col.lower() for p in possibles):
                column_mapping[standard] = col
                found = True
                break
        if not found:
            missing.append(standard)
    
    return len(missing) == 0, column_mapping, missing

def standardize_columns(df, column_mapping=None):
    df = df.copy()
    if column_mapping:
        for standard, actual in column_mapping.items():
            if actual in df.columns:
                df[standard] = df[actual]
    
    for col in ALL_STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = None
    
    return df[ALL_STANDARD_COLUMNS]

def load_data(uploaded_file=None):
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            is_valid, mapping, errors = validate_columns(df)
            if not is_valid:
                st.warning(f"⚠️ Missing columns: {', '.join(errors)}")
            
            df = standardize_columns(df, mapping)
            st.session_state.uploaded_df = df
            st.session_state.data_source = "uploaded"
            st.success(f"✅ Loaded {len(df)} risks")
            return df
        except Exception as e:
            st.error(f"❌ Upload failed: {e}")
            return pd.DataFrame(columns=ALL_STANDARD_COLUMNS)
    else:
        try:
            if os.path.exists(EXCEL_FILE):
                df = pd.read_excel(EXCEL_FILE)
                df = standardize_columns(df)
                st.session_state.data_source = "local"
                return df
            else:
                return pd.DataFrame(columns=ALL_STANDARD_COLUMNS)
        except:
            return pd.DataFrame(columns=ALL_STANDARD_COLUMNS)

def save_data(df):
    try:
        df = standardize_columns(df)
        os.makedirs(os.path.dirname(EXCEL_FILE), exist_ok=True)
        df.to_excel(EXCEL_FILE, index=False)
        st.success("💾 Data saved!")
    except Exception as e:
        st.error(f"❌ Save failed: {e}")