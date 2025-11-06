import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils.helpers import format_date

def generate_burndown(df):
    """Generate burndown data"""
    if df.empty:
        return None, None, None
    
    # Date conversion
    for col in ['Risk Open Date', 'Expected End Date (DD-MMM-YY)', 'Closure Date (DD-MMM-YY)']:
        df[col] = pd.to_datetime(df[col], format="%d-%b-%y", errors='coerce')
    
    min_date = df['Risk Open Date'].min()
    max_date = max(df['Expected End Date (DD-MMM-YY)'].max(), 
                   df['Closure Date (DD-MMM-YY)'].max() or df['Expected End Date (DD-MMM-YY)'].max())
    
    timeline = pd.date_range(start=min_date, end=max_date, freq='D')
    expected_counts, actual_counts = [], []
    
    for date in timeline:
        # Expected open risks
        expected = df[(df['Risk Open Date'] <= date) & 
                     (df['Expected End Date (DD-MMM-YY)'] > date)].shape[0]
        # Actual open risks
        actual = df[(df['Risk Open Date'] <= date) & 
                   (df['Closure Date (DD-MMM-YY)'].isna() | 
                    (df['Closure Date (DD-MMM-YY)'] > date))].shape[0]
        
        expected_counts.append(expected)
        actual_counts.append(actual)
    
    return timeline, expected_counts, actual_counts

def plot_burndown(timeline, expected, actual, title):
    """Plot burndown chart"""
    if timeline is None:
        st.warning("No data for chart")
        return
    
    fig = go.Figure()
    
    # Expected
    fig.add_trace(go.Scatter(x=timeline, y=expected, mode='lines+markers',
                           name='Expected', line=dict(dash='dash', color='orange')))
    # Actual
    fig.add_trace(go.Scatter(x=timeline, y=actual, mode='lines+markers',
                           name='Actual', line=dict(color='green')))
    
    fig.update_layout(
        title=title,
        xaxis_title='Date', yaxis_title='Open Risks',
        height=500, template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def generate_monthly_metrics(df):
    """Generate monthly metrics"""
    df['YearMonth'] = pd.to_datetime(df['Risk Open Date'], format="%d-%b-%y").dt.to_period('M')
    return df.groupby('YearMonth').size()

def plot_monthly_metrics(monthly_data, title):
    """Plot monthly metrics"""
    fig = go.Figure(data=[go.Bar(x=monthly_data.index.astype(str), y=monthly_data.values)])
    fig.update_layout(title=title, xaxis_title='Month', yaxis_title='Risks Opened')
    st.plotly_chart(fig, use_container_width=True)

def render_summary(df):
    """Render summary metrics"""
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total", len(df))
    with col2: st.metric("Open", df['Closure Date (DD-MMM-YY)'].isna().sum())
    with col3: st.metric("Closed", df['Closure Date (DD-MMM-YY)'].notna().sum())