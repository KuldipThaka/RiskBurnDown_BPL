import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data import load_data, save_data
from config.settings import ALL_STANDARD_COLUMNS

def render_dashboard(df):
    """**EXACT SAME DASHBOARD AS ORIGINAL CODE**"""
    st.title("📉 Risk Burndown Dashboard")
    
    # Data source selection with drag & drop
    st.subheader("📁 Choose Data Source")
    col1, col2 = st.columns([2, 1])
    
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
                    st.toast(f"✅ Loaded {len(df)} risks from uploaded file!", icon="✅")
    
    with col2:
        if st.button("💾 Save Current Data to Local", use_container_width=True):
            save_data(df)
    
    # Load data
    if st.session_state.data_source == "local" or st.session_state.uploaded_df is None:
        df = load_data()
    else:
        df = st.session_state.uploaded_df.copy()
    
    # Ensure all columns
    for col in ALL_STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[ALL_STANDARD_COLUMNS]
    
    if df.empty:
        st.info("📤 No risks available. Please add risks on the 'Add Risk' page.")
        st.stop()
    
    # Show data source info
    st.info(f"**Data Source**: {'📁 Local File' if st.session_state.data_source == 'local' else '📤 Uploaded File'} | **Records**: {len(df)}")
    
    # Filter data for tech_manager
    if st.session_state.user_type == 'tech':
        df = df[df['Risk Type'] == 'Technical'].copy()
    
    st.subheader("📄 Data Preview")
    st.dataframe(df)
    
    # Date conversion
    try:
        df['Expected End Date (DD-MMM-YY)'] = pd.to_datetime(df['Expected End Date (DD-MMM-YY)'], format="%d-%b-%y", errors='coerce')
        df['Closure Date (DD-MMM-YY)'] = pd.to_datetime(df['Closure Date (DD-MMM-YY)'], format="%d-%b-%y", errors='coerce')
        df['Risk Open Date'] = pd.to_datetime(df['Risk Open Date'], format="%d-%b-%y", errors='coerce')
    except:
        st.error("❌ Date conversion failed. Please make sure all dates are in DD-MMM-YY format.")
        st.stop()
    
    # Filter into Technical and Business (for upper_manager only)
    df_tech = df[df['Risk Type'] == 'Technical'].copy()
    df_bus = df.copy()  # For upper_manager, df_bus is all risks
    
    # Function to generate burndown data
    def generate_burndown(df_part):
        if df_part.empty:
            return None, None, None
        
        min_date = df_part['Risk Open Date'].min()
        max_date = max(df_part['Expected End Date (DD-MMM-YY)'].max(), 
                      df_part['Closure Date (DD-MMM-YY)'].max() if df_part['Closure Date (DD-MMM-YY)'].notna().any() 
                      else df_part['Expected End Date (DD-MMM-YY)'].max())
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
    
    # IMPROVED Function to plot burndown with Plotly - FIXED PEAK OVERLAP
    def plot_burndown(timeline, expected_counts, actual_counts, title, df_part=None):
        if timeline is None:
            st.warning(f"No data available for {title}")
            return
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add expected burndown (line + bar)
        fig.add_trace(go.Scatter(
            x=timeline, y=expected_counts,
            mode='lines+markers',
            name='Expected Burndown',
            line=dict(dash='dash', color='orange'),
            hovertemplate='<b>Expected</b><br>Date: %{x|%Y-%m-%d}<br>Open Risks: %{y}<extra></extra>'
        ))
        fig.add_trace(go.Bar(
            x=timeline, y=expected_counts,
            name='Expected Bar', opacity=0.3, marker_color='orange'
        ))
        
        # Add actual burndown (line + bar)
        fig.add_trace(go.Scatter(
            x=timeline, y=actual_counts,
            mode='lines+markers',
            name='Actual Burndown',
            line=dict(color='green'),
            hovertemplate='<b>Actual</b><br>Date: %{x|%Y-%m-%d}<br>Open Risks: %{y}<extra></extra>'
        ))
        fig.add_trace(go.Bar(
            x=timeline, y=actual_counts,
            name='Actual Bar', opacity=0.3, marker_color='green'
        ))
        
        # IMPROVED PEAK HANDLING - No overlapping text labels
        if actual_counts:
            peak_threshold = max(actual_counts) * 0.8
            peaks_indices = [i for i, count in enumerate(actual_counts) if count >= peak_threshold]
            
            if peaks_indices:
                # Add visual peak markers only (no text to avoid overlap)
                peak_x = [timeline[i] for i in peaks_indices]
                peak_y = [actual_counts[i] for i in peaks_indices]
                
                fig.add_trace(go.Scatter(
                    x=peak_x, y=peak_y,
                    mode='markers',
                    name='⚠️ Risk Peaks',
                    marker=dict(
                        color='red', 
                        size=15, 
                        symbol='star',
                        line=dict(color='darkred', width=2)
                    ),
                    hovertemplate='<b>🔴 RISK PEAK</b><br>' +
                                 'Date: %{x|%Y-%m-%d}<br>' +
                                 'Open Risks: %{y}<br>' +
                                 'Status: <b>High Risk Period</b><extra></extra>',
                    showlegend=True
                ))
                
                # Display peak summary in expandable section (no chart text overlap)
                peak_summary = []
                for i in peaks_indices:
                    date_str = timeline[i].strftime('%Y-%m-%d')
                    risk_count = actual_counts[i]
                    peak_summary.append((date_str, risk_count))
                
                with st.expander(f"📍 {len(peaks_indices)} Peak Risk Periods Found - Click for Details"):
                    st.markdown("**High Risk Periods (Top 20% of open risks):**")
                    for date_str, risk_count in peak_summary:
                        st.markdown(f"**• {date_str}: {risk_count} open risks**")
                    
                    # Show risks active during the highest peak
                    if peaks_indices and df_part is not None:
                        highest_peak_idx = max(peaks_indices, key=lambda i: actual_counts[i])
                        highest_peak_date = timeline[highest_peak_idx]
                        st.markdown(f"**🔍 Risks active during highest peak ({highest_peak_date.strftime('%Y-%m-%d')}):**")
                        
                        peak_risks = df_part[
                            (df_part['Risk Open Date'] <= highest_peak_date) &
                            (
                                df_part['Closure Date (DD-MMM-YY)'].isna() |
                                (df_part['Closure Date (DD-MMM-YY)'] > highest_peak_date)
                            )
                        ]
                        if not peak_risks.empty:
                            st.dataframe(peak_risks[['Risk ID', 'Risk Description', 'Risk Type', 'Priority', 'Owner']].head(10))
                            if len(peak_risks) > 10:
                                st.info(f"Showing top 10 of {len(peak_risks)} risks.")
        
        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Number of Open Risks',
            hovermode='x unified',
            showlegend=True,
            height=600,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Date selector
        selected_date = st.date_input("🔍 Select a specific date for risk details:", value=timeline[-1].date())
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
                with st.expander(f"📋 {len(open_risks_on_date)} Open Risks on {selected_date}"):
                    st.dataframe(open_risks_on_date[['Risk ID', 'Risk Description', 'Risk Type', 
                                                   'Priority', 'Owner', 'Probability', 'Impact']])
    
    # Function to generate monthly metrics
    def generate_monthly_metrics(df_part):
        if df_part.empty:
            return None, None, None
        
        df_part['YearMonth'] = df_part['Risk Open Date'].dt.to_period('M')
        monthly_risks_opened = df_part.groupby('YearMonth').size()
        avg_rpm = monthly_risks_opened.mean()
        
        min_date = df_part['Risk Open Date'].min()
        max_date = max(df_part['Expected End Date (DD-MMM-YY)'].max(), 
                      df_part['Closure Date (DD-MMM-YY)'].max() if df_part['Closure Date (DD-MMM-YY)'].notna().any() 
                      else df_part['Expected End Date (DD-MMM-YY)'].max())
        monthly_timeline = pd.period_range(start=min_date.to_period('M'), end=max_date.to_period('M'), freq='M')
        
        monthly_expected_open = []
        monthly_actual_open = []
        
        for month in monthly_timeline:
            month_start = month.to_timestamp()
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
            'Risks Opened': monthly_risks_opened.reindex(monthly_timeline, fill_value=0).values,
            'Expected Open Risks': monthly_expected_open,
            'Actual Open Risks': monthly_actual_open
        })
        
        return monthly_timeline, monthly_rpm_df, avg_rpm
    
    # Function to plot monthly metrics with Plotly
    def plot_monthly_metrics(monthly_timeline, monthly_rpm_df, title):
        if monthly_timeline is None:
            st.warning(f"No data available for {title}")
            return
        
        fig = go.Figure()
        
        # Add bars for Risks Opened, Expected, and Actual
        fig.add_trace(go.Bar(
            x=monthly_rpm_df['YearMonth'], y=monthly_rpm_df['Risks Opened'],
            name='Risks Opened', marker_color='blue', opacity=0.7
        ))
        fig.add_trace(go.Bar(
            x=monthly_rpm_df['YearMonth'], y=monthly_rpm_df['Expected Open Risks'],
            name='Expected Open Risks', marker_color='orange', opacity=0.7
        ))
        fig.add_trace(go.Bar(
            x=monthly_rpm_df['YearMonth'], y=monthly_rpm_df['Actual Open Risks'],
            name='Actual Open Risks', marker_color='green', opacity=0.7
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Year-Month',
            yaxis_title='Number of Risks',
            barmode='group',
            xaxis_tickangle=45,
            hovermode='x unified',
            height=500,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Conditional dashboard display based on user type
    if st.session_state.user_type == 'tech':
        # Only show Technical Risks
        st.subheader("🔧 Technical Risk Burndown")
        timeline_tech, expected_tech, actual_tech = generate_burndown(df_tech)
        plot_burndown(timeline_tech, expected_tech, actual_tech, "Technical Risk Burndown Chart", df_part=df_tech)
        
        monthly_timeline_tech, monthly_rpm_df_tech, avg_rpm_tech = generate_monthly_metrics(df_tech)
        if monthly_timeline_tech is not None:
            st.subheader("📈 Monthly RPM (Technical Risks)")
            st.markdown(f"**Average Risks Opened Per Month (RPM): {avg_rpm_tech:.2f}**")
            plot_monthly_metrics(monthly_timeline_tech, monthly_rpm_df_tech, "Monthly Technical Risks Metrics")
            st.write("**Monthly Technical Risk Details:**")
            st.dataframe(monthly_rpm_df_tech.set_index('YearMonth'))
        
        # Summary for Technical
        if not df_tech.empty:
            total_tech = df_tech.shape[0]
            closed_tech = df_tech['Closure Date (DD-MMM-YY)'].notna().sum()
            open_tech = total_tech - closed_tech
            st.subheader("📊 Technical Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Technical Risks", total_tech)
            with col2:
                st.metric("Currently Open", open_tech)
            with col3:
                st.metric("Closed", closed_tech)
    
    else:  # upper_manager
        # Show both Technical and Business (all risks) tabs
        tab1, tab2 = st.tabs(["🔧 Technical Risks", "💼 Business Risks (All)"])
        
        with tab1:
            st.subheader("🔧 Technical Risk Burndown")
            timeline_tech, expected_tech, actual_tech = generate_burndown(df_tech)
            plot_burndown(timeline_tech, expected_tech, actual_tech, "Technical Risk Burndown Chart", df_part=df_tech)
            
            monthly_timeline_tech, monthly_rpm_df_tech, avg_rpm_tech = generate_monthly_metrics(df_tech)
            if monthly_timeline_tech is not None:
                st.subheader("📈 Monthly RPM (Technical Risks)")
                st.markdown(f"**Average Risks Opened Per Month (RPM): {avg_rpm_tech:.2f}**")
                plot_monthly_metrics(monthly_timeline_tech, monthly_rpm_df_tech, "Monthly Technical Risks Metrics")
                st.write("**Monthly Technical Risk Details:**")
                st.dataframe(monthly_rpm_df_tech.set_index('YearMonth'))
            
            # Summary for Technical
            if not df_tech.empty:
                total_tech = df_tech.shape[0]
                closed_tech = df_tech['Closure Date (DD-MMM-YY)'].notna().sum()
                open_tech = total_tech - closed_tech
                st.subheader("📊 Technical Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Technical Risks", total_tech)
                with col2:
                    st.metric("Currently Open", open_tech)
                with col3:
                    st.metric("Closed", closed_tech)
        
        with tab2:
            st.subheader("💼 Business Risk Burndown (All Risks)")
            timeline_bus, expected_bus, actual_bus = generate_burndown(df_bus)
            plot_burndown(timeline_bus, expected_bus, actual_bus, "Business Risk Burndown Chart (All Risks)", df_part=df_bus)
            
            monthly_timeline_bus, monthly_rpm_df_bus, avg_rpm_bus = generate_monthly_metrics(df_bus)
            if monthly_timeline_bus is not None:
                st.subheader("📈 Monthly RPM (All Risks)")
                st.markdown(f"**Average Risks Opened Per Month (RPM): {avg_rpm_bus:.2f}**")
                plot_monthly_metrics(monthly_timeline_bus, monthly_rpm_df_bus, "Monthly All Risks Metrics")
                st.write("**Monthly All Risk Details:**")
                st.dataframe(monthly_rpm_df_bus.set_index('YearMonth'))
            
            # Summary for All Risks
            if not df_bus.empty:
                total_bus = df_bus.shape[0]
                closed_bus = df_bus['Closure Date (DD-MMM-YY)'].notna().sum()
                open_bus = total_bus - closed_bus
                st.subheader("📊 All Risks Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Risks", total_bus)
                with col2:
                    st.metric("Currently Open", open_bus)
                with col3:
                    st.metric("Closed", closed_bus)