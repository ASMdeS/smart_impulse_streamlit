import streamlit as st


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
    percentage_return = (((sum_amount) / sum_investment) - 1) * 100

    with col1:
        st.metric(label=f'Total Amount', value=sum_amount)

    with col2:
        st.metric(label=f'Total Investment', value=sum_investment)

    with col3:
        st.metric(label=f'Total Return', value=f'{percentage_return:.2f}%')
