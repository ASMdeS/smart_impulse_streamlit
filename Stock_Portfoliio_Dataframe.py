import streamlit as st


def generate_summarized_visualization(portfolio_dataframe):
    # Filter rows where 'Sell Date' is missing (assuming the column is named 'Sell Date')
    filtered_dataframe = portfolio_dataframe[portfolio_dataframe['Sell Date'].isna()].sort_values('Buy Date', ascending=False)

    # Select only the columns 'a', 'b', and 'c'
    filtered_dataframe = filtered_dataframe[
        ['Days Holding', 'ROI', 'Sector', 'Market Cap', 'Total Amount', 'Investment']]

    # Tabela de Portfólio no topo
    st.header(f'Stock Portfolio', divider='gray')

    def color_negative_red(value):
        color = 'red' if value < 0 else 'green'
        return f'color: {color}'

    col1, col2 = st.columns(2)
    with col1:  # Apply coloring and formatting
        colored_portfolio = filtered_dataframe.style.applymap(color_negative_red, subset=['ROI'])
        colored_portfolio = colored_portfolio.format({'ROI': '{:.2f}%'})
        colored_portfolio = colored_portfolio.format({'Allocation': '{:.2f}'})

        # Display dataframe
        st.dataframe(data=colored_portfolio, height=300)

    with col2:
        sum_amount = int(filtered_dataframe["Total Amount"].sum())
        sum_investment = int(filtered_dataframe["Investment"].sum())
        percentage_return = ((sum_amount / sum_investment) - 1) * 100

        st.metric(label=f'Total Amount', value=sum_amount)

        st.metric(label=f'Total Investment', value=sum_investment)

        st.metric(label=f'Total Return', value=f'{percentage_return:.2f}%')


def generate_dataframe_visualization(portfolio_dataframe):
    # Tabela de Portfólio no topo
    st.header(f'Stock Portfolio', divider='gray')

    def color_negative_red(value):
        color = 'red' if value < 0 else 'green'
        return f'color: {color}'

    colored_portfolio = portfolio_dataframe.style.applymap(color_negative_red, subset=['ROI'])
    colored_portfolio = colored_portfolio.format({'ROI': '{:.2f}%'})
    colored_portfolio = colored_portfolio.format({'Allocation': '{:.2f}'})
    st.dataframe(data=colored_portfolio, height=300)

    col1, col2, col3 = st.columns(3)

    sum_amount = int(portfolio_dataframe["Total Amount"].sum())
    sum_investment = int(portfolio_dataframe["Investment"].sum())
    percentage_return = ((sum_amount / sum_investment) - 1) * 100

    with col1:
        st.metric(label=f'Total Amount', value=sum_amount)

    with col2:
        st.metric(label=f'Total Investment', value=sum_investment)

    with col3:
        st.metric(label=f'Total Return', value=f'{percentage_return:.2f}%')
