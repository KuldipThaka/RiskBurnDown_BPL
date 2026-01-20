# ---------------------------------------
# Import required libraries
# ---------------------------------------
import pandas as pd
import streamlit as st
import os

# Application-level configuration:
# - EXCEL_FILE: path where risk data is stored locally
# - ALL_STANDARD_COLUMNS: canonical column order used across the app
from config.settings import EXCEL_FILE, ALL_STANDARD_COLUMNS


# ---------------------------------------
# Validate uploaded file columns
# ---------------------------------------
def validate_columns(df):
    """
    Validates whether the uploaded DataFrame contains
    all required risk-related columns.

    Supports flexible column naming by matching
    possible variations of each standard column.
    """

    # Mapping of standard column names to possible variations
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
    
    # Stores mapping: {standard_column: actual_column_in_file}
    column_mapping = {}

    # List of missing required standard columns
    missing = []
    
    # Loop through each standard column definition
    for standard, possibles in required_mapping.items():
        found = False

        # Check against all columns in uploaded DataFrame
        for col in df.columns:
            # Case-insensitive partial match
            if any(p.lower() in col.lower() for p in possibles):
                column_mapping[standard] = col
                found = True
                break

        # Track missing columns
        if not found:
            missing.append(standard)
    
    # Return:
    # - Whether all required columns exist
    # - Mapping from standard → actual column
    # - List of missing columns
    return len(missing) == 0, column_mapping, missing


# ---------------------------------------
# Standardize DataFrame columns
# ---------------------------------------
def standardize_columns(df, column_mapping=None):
    """
    Converts input DataFrame into a standardized format
    using ALL_STANDARD_COLUMNS.

    - Renames/mirrors detected columns
    - Adds missing columns as None
    - Ensures consistent column order
    """

    # Work on a copy to avoid mutating original DataFrame
    df = df.copy()

    # If column mapping exists (from uploaded file),
    # copy actual column values into standard columns
    if column_mapping:
        for standard, actual in column_mapping.items():
            if actual in df.columns:
                df[standard] = df[actual]
    
    # Ensure all standard columns exist
    for col in ALL_STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = None
    
    # Return DataFrame with strict column order
    return df[ALL_STANDARD_COLUMNS]


# ---------------------------------------
# Load data (uploaded or local file)
# ---------------------------------------
def load_data(uploaded_file=None):
    """
    Loads risk data either from:
    - Uploaded file (CSV / Excel)
    - Local Excel file (fallback)

    Also updates Streamlit session_state
    with data source information.
    """

    # Case 1: User uploads a file
    if uploaded_file:
        try:
            # Determine file type and read accordingly
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            # Validate uploaded file columns
            is_valid, mapping, errors = validate_columns(df)

            # Warn user if required columns are missing
            if not is_valid:
                st.warning(f"⚠️ Missing columns: {', '.join(errors)}")
            
            # Standardize columns to app schema
            df = standardize_columns(df, mapping)

            # Save uploaded data to session
            st.session_state.uploaded_df = df
            st.session_state.data_source = "uploaded"

            st.success(f"✅ Loaded {len(df)} risks")
            return df

        except Exception as e:
            # Handle any parsing or validation errors
            st.error(f"❌ Upload failed: {e}")
            return pd.DataFrame(columns=ALL_STANDARD_COLUMNS)

    # Case 2: Load local Excel file
    else:
        try:
            if os.path.exists(EXCEL_FILE):
                df = pd.read_excel(EXCEL_FILE)

                # Normalize columns to standard format
                df = standardize_columns(df)

                st.session_state.data_source = "local"
                return df
            else:
                # No local file → return empty structured DataFrame
                return pd.DataFrame(columns=ALL_STANDARD_COLUMNS)

        except:
            # Safe fallback on read failure
            return pd.DataFrame(columns=ALL_STANDARD_COLUMNS)


# ---------------------------------------
# Save data to local Excel file
# ---------------------------------------
def save_data(df):
    """
    Saves standardized risk data to local Excel file.
    Creates directories if they do not exist.
    """

    try:
        # Ensure DataFrame matches standard schema
        df = standardize_columns(df)

        # Create parent directory if missing
        os.makedirs(os.path.dirname(EXCEL_FILE), exist_ok=True)

        # Save to Excel
        df.to_excel(EXCEL_FILE, index=False)

        st.success("💾 Data saved!")

    except Exception as e:
        # Handle file write errors
        st.error(f"❌ Save failed: {e}")
