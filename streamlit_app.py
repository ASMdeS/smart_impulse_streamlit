import os
from firebase_admin import credentials, storage, initialize_app, _apps, get_app
import streamlit as st
from Creating_Portfolio import excel_to_dataframe, create_portfolio, update_portfolio
import pandas as pd
import math
import plotly.graph_objects as go
from datetime import timedelta
from Donut_Charts import plot_charts
from Growth_Tables import generate_tables
from Stock_Portfoliio_Dataframe import generate_dataframe_visualization
from Getting_Returns import create_mean_cumulative_returns

# Page Settings
st.set_page_config(
    page_title='Portfolio Tracking for Smart Impulse',
    page_icon=':earth_americas:',
    layout="wide"
)

# Set the title that appears at the top of the page and summary of the project.
'''
# :earth_americas: Portfolio Tracking for Smart Impulse

Our project focuses on creating a dynamic, automated Virtual Portfolio (VP) tracking system for Smart Impulse,
aimed at streamlining investment management. The system downloads stock lists daily, automatically identifies
new entries and exits, and manages investments based on predefined conditions. With an initial investment of
$100,000, the portfolio's performance is continuously monitored, and entries are made strategically to maximize
returns. The dashboard provides comprehensive insights, including ROI calculations, top performers and losers,
and portfolio distribution, with real-time updates delivered through Telegram.
'''


# Cache the Firebase initialization to avoid multiple initializations
@st.cache_resource(ttl=timedelta(hours=24))
def init_firebase():
    if not _apps:  # Check if no Firebase app is initialized
        firebase_credentials = dict(st.secrets["firebase"]['my_project_settings'])
        cred = credentials.Certificate(firebase_credentials)
        return initialize_app(cred, {
            'storageBucket': 'smt-bot-staging'
        })
    else:
        return get_app()


# Initialize Firebase
firebase_app = init_firebase()

# Access the Storage bucket
bucket = storage.bucket()

# Folder and local paths
folder_path = 'smart_impulse'
data_dir = 'data'
csv_file_path = os.path.join(data_dir, 'smart_portfolio.csv')

# Ensure the 'data' directory exists
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Check if the smart portfolio CSV already exists
if os.path.exists(csv_file_path):
    # Load the existing portfolio from CSV
    smart_portfolio = pd.read_csv(csv_file_path, index_col=0)
    porfolio_created = True
    print("Smart portfolio loaded from CSV.")
else:
    smart_portfolio = pd.DataFrame()  # Start with an empty DataFrame
    porfolio_created = False

# List all files in the specified folder in Firebase Storage
blobs = list(bucket.list_blobs(prefix=folder_path))

# Get the list of files already downloaded in the "data" directory
local_files = os.listdir(data_dir)

# Download files not in the "data" directory
for blob in blobs:
    original_filename = os.path.basename(blob.name)

    if original_filename:  # Skip directories or empty filenames
        new_filename = original_filename[-15:]

        # Download only if the file does not exist locally
        if new_filename not in local_files:
            local_path = os.path.join(data_dir, new_filename)
            blob.download_to_filename(local_path)
            print(f'File downloaded to {local_path}')
            new_dataframe = excel_to_dataframe(local_path)

            # Create or update the portfolio
            if smart_portfolio.empty:
                smart_portfolio = create_portfolio(new_dataframe, 1 / len(new_dataframe), new_filename[:10])
            else:
                smart_portfolio = update_portfolio(smart_portfolio, new_dataframe, new_filename[:10])

            # Save the portfolio to CSV after every update
            smart_portfolio.to_csv(csv_file_path)
            print(f'Smart portfolio updated and saved to {csv_file_path}')
            local_files = os.listdir(data_dir)

print('All missing files have been downloaded.')

# Print the portfolio on the dataframe
generate_dataframe_visualization(smart_portfolio)


# Cache stock data to avoid multiple Yahoo! Finance requests
@st.cache_data(ttl=timedelta(hours=24))
def get_stock_data():
    # Generate returns and cumulative returns
    smart_returns, smart_cumulative_returns = create_mean_cumulative_returns(smart_portfolio)
    stock_df = smart_returns.T.reset_index()
    stock_df = stock_df.rename(columns={'index': 'Date'})
    stock_df['Date'] = pd.to_datetime(stock_df['Date'])
    return stock_df, smart_cumulative_returns


# Getting the stock data DataFrames
stock_df, stock_returns = get_stock_data()

print(stock_returns)

# Timeframe selection
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

# Filtering DataFrame
filtered_stock_df = stock_df[(stock_df['Date'].dt.date >= from_date) & (stock_df['Date'].dt.date <= to_date)]
filtered_stock_returns = stock_returns[(stock_returns.index >= from_date) & (stock_returns.index <= to_date)]
tickers = stock_df.columns[1:]

if not len(tickers):
    st.warning("No stocks available to select")

selected_stocks = st.multiselect('Which stocks would you like to view?', tickers, [])

if selected_stocks:
    filtered_stock_df = filtered_stock_df[['Date'] + selected_stocks]

# Stock Prices Line Chart
st.header('Stock Prices over Time', divider='gray')
st.line_chart(filtered_stock_df.set_index('Date'))

# Returns of the selected stocks
if selected_stocks:
    st.header(f'Selected Stocks Returns', divider='gray')
    cols = st.columns(4)
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

# Top 10 Tables
generate_tables(filtered_stock_df)

# Backtracking Graph
st.header('Backtracking Portfolio vs Main Indexes', divider='gray')
st.line_chart(filtered_stock_returns)

# Plot Market Sector and Cap Distribution
plot_charts(smart_portfolio)
