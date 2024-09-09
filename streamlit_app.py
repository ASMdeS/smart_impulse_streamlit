import os
import firebase_admin
from firebase_admin import credentials, storage
import streamlit as st
import Creating_Portfolio
import pandas as pd
import math
import plotly.graph_objects as go
from datetime import timedelta


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

# Cache the Firebase initialization to avoid multiple initializations
@st.cache_resource
def init_firebase():
    firebase_credentials = dict(st.secrets["firebase"]['my_project_settings'])
    cred = credentials.Certificate(firebase_credentials)
    # Initialize the Firebase Admin SDK (cached)
    return firebase_admin.initialize_app(cred, {
        'storageBucket': 'smt-bot-staging'
    })

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
            new_dataframe = Creating_Portfolio.excel_to_dataframe(local_path)

            # Create or update the portfolio
            if smart_portfolio.empty:
                smart_portfolio = Creating_Portfolio.create_portfolio(new_dataframe)
            else:
                smart_portfolio = Creating_Portfolio.update_portfolio(smart_portfolio, new_dataframe)

            # Save the portfolio to CSV after every update
            smart_portfolio.to_csv(csv_file_path)
            print(f'Smart portfolio updated and saved to {csv_file_path}')
            local_files = os.listdir(data_dir)

print('All missing files have been downloaded.')

# Generate returns and cumulative returns
smart_returns = Creating_Portfolio.create_returns(smart_portfolio)
smart_cumulative_returns = Creating_Portfolio.create_mean_cumulative_returns(smart_portfolio)


@st.cache_data
def get_stock_data():
    stock_df = smart_returns.T.reset_index()
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


colored_portfolio = smart_portfolio.style.applymap(color_negative_red, subset=['Combined ROI'])
colored_portfolio = colored_portfolio.format({'Combined ROI': '{:.2f}%'})
st.dataframe(data=colored_portfolio, height=300)

col1, col2, col3, col4 = st.columns(4)

sum_amount = int(smart_portfolio["Total Amount"].sum())
sum_investment = int(smart_portfolio["Investment"].sum())
sum_sold = int(smart_portfolio["Sell Value"].sum())
percentage_return = (((sum_amount + sum_sold) / sum_investment) - 1) * 100

with col1:
    st.metric(label=f'Total Amount', value=sum_amount)

with col2:
    st.metric(label=f'Total Investment', value=sum_investment)

with col3:
    st.metric(label=f'Total Sold', value=sum_sold)

with col4:
    st.metric(label=f'Total Investment', value=f'{percentage_return:.2f}%')

# Gráfico de Preços das Ações
st.header('Stock Prices over Time', divider='gray')
st.line_chart(filtered_stock_df.set_index('Date'))

# Retornos das Ações Selecionadas
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


# Criação de um DataFrame vazio
growth_data = []

for ticker in tickers:
    first_price = filtered_stock_df[ticker].iloc[0]
    last_price = filtered_stock_df[ticker].iloc[-1]

    if not pd.isna(first_price) and not pd.isna(last_price) and first_price != 0:
        growth = (last_price - first_price) / first_price * 100
        # Em vez de append, armazenamos os dados em uma lista
        growth_data.append({'Stock': ticker, 'Growth (%)': growth})

# Agora criamos o DataFrame a partir da lista
growth_df = pd.DataFrame(growth_data)

# Classificar as 10 ações com maior crescimento
top_10_growth = growth_df.sort_values(by='Growth (%)', ascending=False).head(10).reset_index(drop=True)
top_10_growth.index = top_10_growth.index + 1

# Classificar as 10 ações com pior desempenho
worst_10_growth = growth_df.sort_values(by='Growth (%)', ascending=True).head(10).reset_index(drop=True)
worst_10_growth.index = worst_10_growth.index + 1

col1, col2 = st.columns(2)

with col1:
    # Exibir a tabela das 10 ações com maior crescimento
    st.header('Top 10 Stocks by Growth', divider='gray')
    st.table(top_10_growth)

with col2:
    # Exibir a tabela das 10 ações com pior desempenho
    st.header('Worst 10 Stocks by Growth', divider='gray')
    st.table(worst_10_growth)

# Create two columns
col1, col2 = st.columns(2)

# Prepare data for the donut chart
with col1:
    grouped_by_sector = smart_portfolio.groupby('Sector')['Allocation'].sum()
    labels_cap = grouped_by_sector.index
    values_cap = grouped_by_sector.values

    fig_sector = go.Figure(data=[go.Pie(labels=labels_cap, values=values_cap, hole=.3)])

    st.header('Market Sector Distribution', divider='gray')
    st.plotly_chart(fig_sector)

# Prepare data for the donut chart
with col2:
    grouped_by_cap = smart_portfolio.groupby('Market Cap')['Allocation'].sum()
    labels_cap = grouped_by_cap.index
    values_cap = grouped_by_cap.values

    fig_cap = go.Figure(data=[go.Pie(labels=labels_cap, values=values_cap, hole=.3)])

    st.header('Market Capitalization Distribution', divider='gray')
    st.plotly_chart(fig_cap)
