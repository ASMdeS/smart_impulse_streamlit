# Importing the pandas library
import pandas as pd
import yfinance as yf

pd.set_option('display.max_columns', 500)

# Function to transform csv files in desired dataframes
def csv_to_dataframe(file_name):
    # Transform csv in dataframe
    dataframe = pd.read_csv(file_name)
    # Remove 'Summary' column
    dataframe = dataframe.iloc[:-1]
    # Index the dataframe to the Ticker
    dataframe.set_index('Ticker', inplace=True)
    # Removing the "$" from the 'Price' column
    dataframe['Price'] = dataframe['Price'].apply(lambda x: float(x[1:]) if isinstance(x, str) else x)
    # Returning the Dataframe
    return dataframe

# Function to create the portfolio dataframe
def create_portfolio(initial_dataframe):
    portfolio = initial_dataframe.index.to_frame(index=True)
    portfolio['Sector'] = initial_dataframe['Sector']
    portfolio['Allocation'] = 1 / len(initial_dataframe)
    portfolio['Value'] = portfolio['Allocation'] * 100000
    portfolio['Overdraft'] = 0
    portfolio['Yesterday Price'] = None
    portfolio['Today Price'] = initial_dataframe['Price']
    portfolio['Sell Price'] = None
    portfolio['First Entry'] = True
    portfolio['First Entry Price'] = initial_dataframe['Price']
    portfolio['Days Since First Entry'] = 0
    portfolio['Second Entry'] = False
    portfolio['Second Entry Price'] = None
    portfolio['Days Since Second Entry'] = 0
    portfolio['Third Entry'] = False
    portfolio['Third Entry Price'] = None
    portfolio['Quantity'] = portfolio['Value'] / portfolio['First Entry Price']
    # Creating the Stock Returns Dataframe
    data = yf.download(portfolio.index.tolist(), start="2022-01-01", end="2023-01-01")
    # Extract the 'Close' prices
    close_prices = data['Close']
    # Transpose the DataFrame so that tickers are the index and dates are columns
    returns = close_prices.T

    return portfolio, returns

def create_returns(initial_dataframe):
    # Download the historical data for each ticker
    data = yf.download(first_day.index.tolist(), start="2022-01-01", end="2023-01-01")

    # Extract the 'Close' prices
    close_prices = data['Close']

    # Transpose the DataFrame so that tickers are the index and dates are columns
    df = close_prices.T

    return df


# Creating the dataframes
first_day = csv_to_dataframe('data/Daily Stocks - first_day.csv')
second_day = csv_to_dataframe('data/Daily Stocks - second_day.csv')
third_day = csv_to_dataframe('data/Daily Stocks - third_day.csv')
fourth_day = csv_to_dataframe('data/Daily Stocks - fourth_day.csv')
fifth_day = csv_to_dataframe('data/Daily Stocks - fifth_day.csv')
sixth_day = csv_to_dataframe('data/Daily Stocks - sixth_day.csv')

smart_portfolio, smart_returns = create_portfolio(first_day)
