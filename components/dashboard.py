# ---------------------------------------
# Imports
# ---------------------------------------
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Data utilities
from utils.data import load_data, save_data

# Standard column schema
from config.settings import ALL_STANDARD_COLUMNS


# ---------------------------------------
# Dashboard Renderer
# ---------------------------------------
def render_dashboard(df):
    """
    Renders the Risk Burndown Dashboard.

    Features:
    - Upload & switch between local / uploaded data
    - Daily and monthly burndown analysis
    - Peak risk detection
    - Role-based dashboard (tech vs upper manager)
    """

    # Page title
    st.title("📉 Risk Burndown Dashboard")
    

    # ---------------------------------------
    # Data Source Selection
    # ---------------------------------------
    st.subheader("📁 Choose Data Source")

    col1, col2 = st.columns([2, 1])

    # Upload external Excel / CSV file
    with col1:
        uploaded_file = st.file_uploader(
            "📤 **Drag & Drop Excel/CSV file here** or click to browse",
            type=['xlsx', 'xls', 'csv'],
            help="Supports .xlsx, .xls, .csv files with risk data"
        )
        
        if uploaded_file is not None:
            with st.spinner("Validating and loading file..."):
                df = load_data(uploaded_file)

                if df is not None:
                    st.session_state.uploaded_df = df
                    st.session_state.data_source = "uploaded"
                    st.toast(
                        f"✅ Loaded {len(df)} risks from uploaded file!",
                        icon="✅"
                    )

    # Save current data to local Excel
    with col2:
        if st.button("💾 Save Current Data to Local", use_container_width=True):
            save_data(df)


    # ---------------------------------------
    # Load active dataset based on source
    # ---------------------------------------
    if (
        st.session_state.data_source == "local"
        or st.session_state.uploaded_df is None
    ):
        df = load_data()
    else:
        df = st.session_state.uploaded_df.copy()


    # ---------------------------------------
    # Ensure schema consistency
    # ---------------------------------------
    for col in ALL_STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df = df[ALL_STANDARD_COLUMNS]


    # ---------------------------------------
    # Empty data handling
    # ---------------------------------------
    if df.empty:
        st.info("📤 No risks available. Please add risks on the 'Add Risk' page.")
        st.stop()


    # ---------------------------------------
    # Data source info banner
    # ---------------------------------------
    st.info(
        f"**Data Source**: "
        f"{'📁 Local File' if st.session_state.data_source == 'local' else '📤 Uploaded File'} "
        f"| **Records**: {len(df)}"
    )


    # ---------------------------------------
    # Role-based filtering
    # ---------------------------------------
    # Tech users only see Technical risks
    if st.session_state.user_type == 'tech':
        df = df[df['Risk Type'] == 'Technical'].copy()


    # ---------------------------------------
    # Data preview
    # ---------------------------------------
    st.subheader("📄 Data Preview")
    st.dataframe(df)


    # ---------------------------------------
    # Date conversion
    # ---------------------------------------
    try:
        df['Expected End Date (DD-MMM-YY)'] = pd.to_datetime(
            df['Expected End Date (DD-MMM-YY)'],
            format="%d-%b-%y",
            errors='coerce'
        )
        df['Closure Date (DD-MMM-YY)'] = pd.to_datetime(
            df['Closure Date (DD-MMM-YY)'],
            format="%d-%b-%y",
            errors='coerce'
        )
        df['Risk Open Date'] = pd.to_datetime(
            df['Risk Open Date'],
            format="%d-%b-%y",
            errors='coerce'
        )
    except:
        st.error("❌ Date conversion failed. Ensure DD-MMM-YY format.")
        st.stop()


    # ---------------------------------------
    # Split datasets
    # ---------------------------------------
    df_tech = df[df['Risk Type'] == 'Technical'].copy()
    df_bus = df.copy()  # All risks for upper manager


    # ---------------------------------------
    # Daily burndown data generator
    # ---------------------------------------
    def generate_burndown(df_part):
        """
        Calculates expected vs actual open risks
        for each day in the timeline.
        """
        if df_part.empty:
            return None, None, None
        
        min_date = df_part['Risk Open Date'].min()
        max_date = max(
            df_part['Expected End Date (DD-MMM-YY)'].max(),
            df_part['Closure Date (DD-MMM-YY)'].max()
            if df_part['Closure Date (DD-MMM-YY)'].notna().any()
            else df_part['Expected End Date (DD-MMM-YY)'].max()
        )

        timeline = pd.date_range(start=min_date, end=max_date, freq='D')

        expected_counts = []
        actual_counts = []

        for current_date in timeline:
            expected_open = df_part[
                (df_part['Risk Open Date'] <= current_date) &
                (df_part['Expected End Date (DD-MMM-YY)'] > current_date)
            ].shape[0]

            actual_open = df_part[
                (df_part['Risk Open Date'] <= current_date) &
                (
                    df_part['Closure Date (DD-MMM-YY)'].isna() |
                    (df_part['Closure Date (DD-MMM-YY)'] > current_date)
                )
            ].shape[0]

            expected_counts.append(expected_open)
            actual_counts.append(actual_open)

        return timeline, expected_counts, actual_counts


    # ---------------------------------------
    # Burndown plotting (Plotly)
    # ---------------------------------------
    def plot_burndown(timeline, expected_counts, actual_counts, title, df_part=None):
        """
        Plots daily expected vs actual burndown,
        highlights peak risk periods,
        and allows date-based drill-down.
        """
        if timeline is None:
            st.warning(f"No data available for {title}")
            return

        fig = go.Figure()

        # Expected burndown
        fig.add_trace(go.Scatter(
            x=timeline,
            y=expected_counts,
            mode='lines+markers',
            name='Expected Burndown',
            line=dict(dash='dash', color='orange')
        ))
        fig.add_trace(go.Bar(
            x=timeline,
            y=expected_counts,
            name='Expected Bar',
            opacity=0.3
        ))

        # Actual burndown
        fig.add_trace(go.Scatter(
            x=timeline,
            y=actual_counts,
            mode='lines+markers',
            name='Actual Burndown',
            line=dict(color='green')
        ))
        fig.add_trace(go.Bar(
            x=timeline,
            y=actual_counts,
            name='Actual Bar',
            opacity=0.3
        ))


        # ---------------------------------------
        # Peak risk detection (top 20%)
        # ---------------------------------------
        if actual_counts:
            peak_threshold = max(actual_counts) * 0.8
            peaks_indices = [
                i for i, count in enumerate(actual_counts)
                if count >= peak_threshold
            ]

            if peaks_indices:
                peak_x = [timeline[i] for i in peaks_indices]
                peak_y = [actual_counts[i] for i in peaks_indices]

                fig.add_trace(go.Scatter(
                    x=peak_x,
                    y=peak_y,
                    mode='markers',
                    name='⚠️ Risk Peaks',
                    marker=dict(
                        color='red',
                        size=15,
                        symbol='star'
                    )
                ))

        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Number of Open Risks',
            hovermode='x unified',
            height=600,
            template='plotly_white'
        )

        st.plotly_chart(fig, use_container_width=True)


        # ---------------------------------------
        # Date-based drill-down
        # ---------------------------------------
        selected_date = st.date_input(
            "🔍 Select a specific date for risk details:",
            value=timeline[-1].date()
        )

        selected_date_dt = pd.to_datetime(selected_date)

        if df_part is not None:
            open_risks_on_date = df_part[
                (df_part['Risk Open Date'] <= selected_date_dt) &
                (
                    df_part['Closure Date (DD-MMM-YY)'].isna() |
                    (df_part['Closure Date (DD-MMM-YY)'] > selected_date_dt)
                )
            ]

            if not open_risks_on_date.empty:
                with st.expander(
                    f"📋 {len(open_risks_on_date)} Open Risks on {selected_date}"
                ):
                    st.dataframe(
                        open_risks_on_date[
                            ['Risk ID', 'Risk Description', 'Risk Type',
                             'Priority', 'Owner', 'Probability', 'Impact']
                        ]
                    )


    # ---------------------------------------
    # Monthly metrics generator
    # ---------------------------------------
    def generate_monthly_metrics(df_part):
        """
        Calculates monthly:
        - Risks opened
        - Expected open risks
        - Actual open risks
        - Average RPM
        """
        if df_part.empty:
            return None, None, None

        df_part['YearMonth'] = df_part['Risk Open Date'].dt.to_period('M')
        monthly_risks_opened = df_part.groupby('YearMonth').size()
        avg_rpm = monthly_risks_opened.mean()

        min_date = df_part['Risk Open Date'].min()
        max_date = max(
            df_part['Expected End Date (DD-MMM-YY)'].max(),
            df_part['Closure Date (DD-MMM-YY)'].max()
            if df_part['Closure Date (DD-MMM-YY)'].notna().any()
            else df_part['Expected End Date (DD-MMM-YY)'].max()
        )

        monthly_timeline = pd.period_range(
            start=min_date.to_period('M'),
            end=max_date.to_period('M'),
            freq='M'
        )

        monthly_expected_open = []
        monthly_actual_open = []

        for month in monthly_timeline:
            month_end = (month + 1).to_timestamp() - pd.Timedelta(days=1)

            expected_open = df_part[
                (df_part['Risk Open Date'] <= month_end) &
                (df_part['Expected End Date (DD-MMM-YY)'] > month_end)
            ].shape[0]

            actual_open = df_part[
                (df_part['Risk Open Date'] <= month_end) &
                (
                    df_part['Closure Date (DD-MMM-YY)'].isna() |
                    (df_part['Closure Date (DD-MMM-YY)'] > month_end)
                )
            ].shape[0]

            monthly_expected_open.append(expected_open)
            monthly_actual_open.append(actual_open)

        monthly_rpm_df = pd.DataFrame({
            'YearMonth': [str(m) for m in monthly_timeline],
            'Risks Opened': monthly_risks_opened.reindex(
                monthly_timeline,
                fill_value=0
            ).values,
            'Expected Open Risks': monthly_expected_open,
            'Actual Open Risks': monthly_actual_open
        })

        return monthly_timeline, monthly_rpm_df, avg_rpm
