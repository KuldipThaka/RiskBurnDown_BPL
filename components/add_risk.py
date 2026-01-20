# ---------------------------------------
# Import required libraries & modules
# ---------------------------------------
import streamlit as st
import pandas as pd

# Data utilities for loading & saving risk data
from utils.data import load_data, save_data

# Configuration options used for dropdowns & formatting
from config.settings import (
    RISK_TYPE_OPTIONS,
    PROBABILITY_OPTIONS,
    IMPACT_OPTIONS,
    DIFFICULTY_OPTIONS,
    PRIORITY_OPTIONS,
    DATE_FORMAT
)

# Helper function for role-based data filtering
from utils.helpers import filter_by_user_type


# ---------------------------------------
# Render "Add Risk" Page
# ---------------------------------------
def render_add_risk(df):  # ✅ Entry point for Add Risk UI
    """
    Renders the Add Risk page which allows:
    - Uploading risk data (Excel/CSV)
    - Manually adding a new risk
    - Saving data locally
    - Viewing current risks (role-filtered)
    """

    # Page title
    st.title("➕ Add New Risk")
    
    # -----------------------------
    # File Upload & Save Controls
    # -----------------------------
    col1, col2 = st.columns([3, 1])

    # File upload section
    with col1:
        uploaded_file = st.file_uploader(
            "📤 Upload Excel/CSV",
            type=['xlsx', 'csv']
        )

        # If user uploads a file, load and standardize it
        if uploaded_file:
            df = load_data(uploaded_file)
    
    # Save button (manual persistence)
    with col2:
        if st.button("💾 Save to Local"):
            save_data(df)
    
    # -----------------------------
    # Default Risk Type (Role-based)
    # -----------------------------
    # Technical users default to "Technical" risk
    # Others default to "Quality"
    default_type = (
        'Technical'
        if st.session_state.get('user_type') == 'tech'
        else 'Quality'
    )

    # -----------------------------
    # Add Risk Form
    # -----------------------------
    with st.form("add_risk_form"):
        st.subheader("📝 Basic Information")

        # Risk ID & Type
        col1, col2 = st.columns(2)
        risk_id = col1.text_input("**Risk ID** *")
        risk_type = col2.selectbox(
            "**Risk Type**",
            RISK_TYPE_OPTIONS,
            index=RISK_TYPE_OPTIONS.index(default_type)
        )
        
        # Risk description & open date
        col1, col2 = st.columns(2)
        risk_desc = col1.text_area(
            "**Risk Description** *",
            height=80
        )
        open_date = col2.date_input("**Open Date** *")
        
        # Expected end date & closure date
        col1, col2 = st.columns(2)
        expected_end = col1.date_input("**Expected End Date** *")
        closure_date = col2.date_input(
            "**Closure Date**",
            value=None
        )
        
        # -----------------------------
        # Risk Assessment Section
        # -----------------------------
        st.subheader("📊 Risk Assessment")

        col1, col2, col3 = st.columns(3)
        probability = col1.selectbox(
            "**Probability**",
            PROBABILITY_OPTIONS
        )
        impact = col2.selectbox(
            "**Impact**",
            IMPACT_OPTIONS
        )
        difficulty = col3.selectbox(
            "**Difficulty**",
            DIFFICULTY_OPTIONS
        )
        
        # Priority & Owner
        col1, col2 = st.columns(2)
        priority = col1.selectbox(
            "**Priority**",
            PRIORITY_OPTIONS
        )
        owner = col2.text_input("**Owner** *")
        
        # Action plan / mitigation steps
        action_plan = st.text_area(
            "**Action Plan**",
            height=100
        )
        
        # -----------------------------
        # Form Submission Logic
        # -----------------------------
        if st.form_submit_button("✅ Add Risk"):
            
            # Mandatory field validation
            if not all([
                risk_id,
                risk_desc,
                owner,
                open_date,
                expected_end
            ]):
                st.error("❌ Fill all required fields")
            
            else:
                # Construct new risk record
                new_row = {
                    'Risk ID': risk_id,
                    'Risk Description': risk_desc,
                    'Risk Open Date': open_date.strftime(DATE_FORMAT),
                    'Expected End Date (DD-MMM-YY)': expected_end.strftime(DATE_FORMAT),
                    'Closure Date (DD-MMM-YY)': (
                        closure_date.strftime(DATE_FORMAT)
                        if closure_date else None
                    ),
                    'Risk Type': risk_type,
                    'Probability': probability,
                    'Impact': impact,
                    'Difficulty': difficulty,
                    'Priority': priority,
                    'Action Plan': action_plan,
                    'Owner': owner
                }
                
                # Append new record to DataFrame
                df = pd.concat(
                    [df, pd.DataFrame([new_row])],
                    ignore_index=True
                )

                # Update session data
                st.session_state.uploaded_df = df

                # Persist data locally
                save_data(df)

                st.success("✅ Risk added!")
                st.rerun()
    
    # -----------------------------
    # Display Current Risks
    # -----------------------------
    # Apply role-based filtering
    filtered_df = filter_by_user_type(df)

    st.subheader("📄 Current Risks")

    if not filtered_df.empty:
        # Display risk table
        st.dataframe(
            filtered_df,
            use_container_width=True
        )

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", len(filtered_df))
        with col2:
            st.metric(
                "Open",
                filtered_df['Closure Date (DD-MMM-YY)'].isna().sum()
            )
        with col3:
            st.metric(
                "High Priority",
                len(
                    filtered_df[
                        filtered_df['Priority'].isin(['High', 'Critical'])
                    ]
                )
            )
    else:
        # No data message
        st.info("No risks yet!")
