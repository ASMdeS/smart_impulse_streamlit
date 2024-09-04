import streamlit as st
import pandas as pd
import math
import plotly.graph_objects as go
from datetime import timedelta
from Updating_Portfolio import third_portfolio, third_returns, third_performers, third_losers

# Configuração da página
st.set_page_config(
    page_title='Portfolio Tracking for Smart Impulse',
    page_icon=':earth_americas:',
    layout="wide"
)

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :earth_americas: Portfolio Tracking for Smart Impulse

Our project focuses on creating a dynamic, automated Virtual Portfolio (VP) tracking system for Smart Impulse,
aimed at streamlining investment management. The system downloads stock lists daily, automatically identifies
new entries and exits, and manages investments based on predefined conditions. With an initial investment of
$100,000, the portfolio's performance is continuously monitored, and entries are made strategically to maximize
returns. The dashboard provides comprehensive insights, including ROI calculations, top performers and losers,
and portfolio distribution, with real-time updates delivered through Telegram.
'''

# Add some spacing
''
''


# Função para obter dados de ações
@st.cache_data
def get_stock_data():
    stock_df = third_returns.T.reset_index()
    stock_df = stock_df.rename(columns={'index': 'Date'})
    stock_df['Date'] = pd.to_datetime(stock_df['Date'])
    return stock_df


stock_df = get_stock_data()

# Seleção de período
min_date = stock_df['Date'].min().date()
max_date = stock_df['Date'].max().date()

period_options = {
    '1 day': timedelta(days=1),
    '1 month': timedelta(days=30),
    '3 months': timedelta(days=90),
    '6 months': timedelta(days=180),
    '1 year': timedelta(days=365),
    '2 years': timedelta(days=730),
    '3 years': timedelta(days=1095),
    'Maximum': max_date - min_date
}

selected_period = st.selectbox('Select the period:', list(period_options.keys()), 4)

if selected_period == 'Maximum':
    from_date = min_date
else:
    from_date = max_date - period_options[selected_period]

to_date = max_date

st.write(f"Displaying data from {from_date} to {to_date}")

# Filtrar DataFrame
filtered_stock_df = stock_df[(stock_df['Date'].dt.date >= from_date) & (stock_df['Date'].dt.date <= to_date)]

tickers = stock_df.columns[1:]

if not len(tickers):
    st.warning("No stocks available to select")

selected_stocks = st.multiselect('Which stocks would you like to view?', tickers, [])

if selected_stocks:
    filtered_stock_df = filtered_stock_df[['Date'] + selected_stocks]

# Tabela de Portfólio no topo
st.header(f'Stock Portfolio', divider='gray')


def color_negative_red(value):
    color = 'red' if value < 0 else 'green'
    return f'color: {color}'


total = third_portfolio.sum(numeric_only=True)
colored_portfolio = third_portfolio.style.applymap(color_negative_red, subset=['Combined ROI'])
colored_portfolio = colored_portfolio.format({'Combined ROI': '{:.2f}%'})
st.dataframe(data=colored_portfolio, height=300)

col1, col2, col3 = st.columns(3)

sum_amount = int(third_portfolio["Total Amount"].sum())
sum_investment = int(third_portfolio["Investment"].sum())
percentage_return = ((sum_investment / sum_amount) - 1) * 100

with col1:
    st.metric(label=f'Total Amount', value=sum_amount)

with col2:
    st.metric(label=f'Total Investment', value=sum_investment)

with col3:
    st.metric(label=f'Total Investment', value=f'{percentage_return:.2f}%')


# Adicionando o total geral
st.write("Total Geral:")
st.write(total)

# Gráfico de Preços das Ações
st.header('Stock Prices over Time', divider='gray')
st.line_chart(filtered_stock_df.set_index('Date'))

# Retornos das Ações Selecionadas
st.header(f'Selected Stocks Returns', divider='gray')

cols = st.columns(4)

if selected_stocks:
    for i, ticker in enumerate(selected_stocks):
        col = cols[i % len(cols)]
        with col:
            first_price = filtered_stock_df.iloc[0][ticker]
            last_price = filtered_stock_df.iloc[-1][ticker]

            if math.isnan(first_price):
                growth = 'n/a'
                delta_color = 'off'
            else:
                growth = f'{last_price / first_price:,.2f}x'
                delta_color = 'normal'

            st.metric(label=f'{ticker} Price', value=f'{last_price:,.2f}', delta=growth, delta_color=delta_color)

# Exibir ações fechadas e desempenho
st.header(f'Closed Positions', divider='gray')
# Aqui você deve adicionar a lógica para exibir as ações fechadas e seu desempenho.

# Exibir top performers e losers
col1, col2 = st.columns(2)

with col1:
    st.subheader(f'Top 10 Performers', divider='grey')
    top_performers_display = third_performers[['Combined ROI']].copy()
    top_performers_display.index.name = 'Ticker'
    st.dataframe(top_performers_display)

with col2:
    st.subheader(f'Top 10 Losers', divider='grey')
    top_losers_display = third_losers[['Combined ROI']].copy()
    top_losers_display.index.name = 'Ticker'
    st.dataframe(top_losers_display)

# Create two columns
col1, col2 = st.columns(2)

# Prepare data for the donut chart
with col1:
    grouped_by_sector = third_portfolio.groupby('Sector')['Allocation'].sum()
    labels_cap = grouped_by_sector.index
    values_cap = grouped_by_sector.values

    fig_sector = go.Figure(data=[go.Pie(labels=labels_cap, values=values_cap, hole=.3)])

    st.header('Market Sector Distribution', divider='gray')
    st.plotly_chart(fig_sector)

# Prepare data for the donut chart
with col2:
    grouped_by_cap = third_portfolio.groupby('Market Cap')['Allocation'].sum()
    labels_cap = grouped_by_cap.index
    values_cap = grouped_by_cap.values

    fig_cap = go.Figure(data=[go.Pie(labels=labels_cap, values=values_cap, hole=.3)])

    st.header('Market Capitalization Distribution', divider='gray')
    st.plotly_chart(fig_cap)
