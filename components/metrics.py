import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils.helpers import format_date


def generate_burndown(df):
    """
    Generate burndown chart data:
    - timeline (date range)
    - expected open risks per day
    - actual open risks per day
    """

    # Handle empty dataframe
    if df.empty:
        return None, None, None

    # Convert relevant date columns to datetime
    for col in [
        'Risk Open Date',
        'Expected End Date (DD-MMM-YY)',
        'Closure Date (DD-MMM-YY)'
    ]:
        df[col] = pd.to_datetime(df[col], format="%d-%b-%y", errors='coerce')

    # Determine timeline start and end dates
    min_date = df['Risk Open Date'].min()

    max_date = max(
        df['Expected End Date (DD-MMM-YY)'].max(),
        df['Closure Date (DD-MMM-YY)'].max()
        or df['Expected End Date (DD-MMM-YY)'].max()
    )

    # Create daily timeline
    timeline = pd.date_range(start=min_date, end=max_date, freq='D')

    expected_counts = []
    actual_counts = []

    # Calculate expected and actual open risks for each date
    for date in timeline:

        # Expected open risks:
        # Opened on/before date AND expected end date is after current date
        expected = df[
            (df['Risk Open Date'] <= date) &
            (df['Expected End Date (DD-MMM-YY)'] > date)
        ].shape[0]

        # Actual open risks:
        # Opened on/before date AND either not closed or closed after current date
        actual = df[
            (df['Risk Open Date'] <= date) &
            (
                df['Closure Date (DD-MMM-YY)'].isna() |
                (df['Closure Date (DD-MMM-YY)'] > date)
            )
        ].shape[0]

        expected_counts.append(expected)
        actual_counts.append(actual)

    return timeline, expected_counts, actual_counts


def plot_burndown(timeline, expected, actual, title):
    """
    Plot burndown chart using Plotly
    """

    # Handle missing data
    if timeline is None:
        st.warning("No data for chart")
        return

    fig = go.Figure()

    # Expected burndown line (dashed)
    fig.add_trace(
        go.Scatter(
            x=timeline,
            y=expected,
            mode='lines+markers',
            name='Expected',
            line=dict(dash='dash', color='orange')
        )
    )

    # Actual burndown line
    fig.add_trace(
        go.Scatter(
            x=timeline,
            y=actual,
            mode='lines+markers',
            name='Actual',
            line=dict(color='green')
        )
    )

    # Layout configuration
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Open Risks',
        height=500,
        template='plotly_white'
    )

    # Render chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)


def generate_monthly_metrics(df):
    """
    Generate count of risks opened per month
    """

    # Create Year-Month column from Risk Open Date
    df['YearMonth'] = pd.to_datetime(
        df['Risk Open Date'],
        format="%d-%b-%y"
    ).dt.to_period('M')

    # Group by month and count risks
    return df.groupby('YearMonth').size()


def plot_monthly_metrics(monthly_data, title):
    """
    Plot monthly risk count bar chart
    """

    fig = go.Figure(
        data=[
            go.Bar(
                x=monthly_data.index.astype(str),
                y=monthly_data.values
            )
        ]
    )

    fig.update_layout(
        title=title,
        xaxis_title='Month',
        yaxis_title='Risks Opened'
    )

    # Render chart
    st.plotly_chart(fig, use_container_width=True)


def render_summary(df):
    """
    Render summary metrics (Total, Open, Closed)
    """

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total", len(df))

    with col2:
        st.metric(
            "Open",
            df['Closure Date (DD-MMM-YY)'].isna().sum()
        )

    with col3:
        st.metric(
            "Closed",
            df['Closure Date (DD-MMM-YY)'].notna().sum()
        )
