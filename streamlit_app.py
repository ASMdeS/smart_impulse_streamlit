import streamlit as st
import pandas as pd
import math
from pathlib import Path
from Updating_Portfolio import second_portfolio, second_returns

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Portfolio Tracking for Smart Impulse',
    page_icon=':earth_americas:',  # This is an emoji shortcode. Could be a URL too.
)


# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_stock_data():
    """Prepare stock data from second_returns DataFrame."""
    # Pivot the DataFrame to have 'Date' as the index and 'Ticker' as columns
    stock_df = second_returns.T.reset_index()
    stock_df = stock_df.rename(columns={'index': 'Date'})
    stock_df['Date'] = pd.to_datetime(stock_df['Date'])
    return stock_df


stock_df = get_stock_data()

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

min_date = stock_df['Date'].min().date()  # Convert to datetime.date
max_date = stock_df['Date'].max().date()  # Convert to datetime.date

# Slider for selecting date range
from_date, to_date = st.slider(
    'Select the date range:',
    min_value=min_date,
    max_value=max_date,
    value=[min_date, max_date],
    format="YYYY-MM-DD"
)

tickers = stock_df.columns[1:]  # Exclude 'Date' column

if not len(tickers):
    st.warning("No stocks available to select")

selected_stocks = st.multiselect(
    'Which stocks would you like to view?',
    tickers,
    [])

''
''
''

# Filter the data
filtered_stock_df = stock_df[
    (stock_df['Date'] >= pd.to_datetime(from_date))
    & (stock_df['Date'] <= pd.to_datetime(to_date))
    ]

if selected_stocks:
    filtered_stock_df = filtered_stock_df[['Date'] + selected_stocks]

st.header('Stock Prices over Time', divider='gray')

''

st.line_chart(
    filtered_stock_df.set_index('Date'),
)

''
''

# Display stock portfolio
st.header(f'Stock Portfolio', divider='gray')
st.dataframe(data=second_portfolio)

''
''

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

            st.metric(
                label=f'{ticker} Price',
                value=f'{last_price:,.2f}',
                delta=growth,
                delta_color=delta_color
            )