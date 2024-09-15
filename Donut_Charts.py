import streamlit as st
import plotly.graph_objects as go


def plot_charts(portfolio_dataframe):
    # Create two columns
    col1, col2 = st.columns(2)

    # Prepare data for the donut chart
    with col1:
        grouped_by_sector = portfolio_dataframe.groupby('Sector')['Allocation'].sum()
        labels_cap = grouped_by_sector.index
        values_cap = grouped_by_sector.values

        fig_sector = go.Figure(data=[go.Pie(labels=labels_cap, values=values_cap, hole=.3)])

        st.header('Market Sector Distribution', divider='gray')
        st.plotly_chart(fig_sector)

    # Prepare data for the donut chart
    with col2:
        grouped_by_cap = portfolio_dataframe.groupby('Market Cap')['Allocation'].sum()
        labels_cap = grouped_by_cap.index
        values_cap = grouped_by_cap.values

        fig_cap = go.Figure(data=[go.Pie(labels=labels_cap, values=values_cap, hole=.3)])

        st.header('Market Capitalization Distribution', divider='gray')
        st.plotly_chart(fig_cap)
