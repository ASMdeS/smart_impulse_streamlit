# Importing the pandas library
# import Firebase
import pandas as pd
import yfinance as yf
import openpyxl
from Telegram_Bot import sold_stocks, bought_stocks

pd.set_option('display.max_columns', 500)


# Function to transform csv files in desired dataframes
def excel_to_dataframe(file_name):
    # Transform csv in dataframe
    dataframe = pd.read_excel(file_name, engine='openpyxl')
    # Remove 'Summary' column
    dataframe = dataframe.iloc[:-1]
    # Index the dataframe to the Ticker
    dataframe.set_index('Ticker', drop=True, inplace=True)
    # Removing the "$" from the 'Price' and 'Market Cap' columns
    dataframe['Price'] = dataframe['Price'].apply(lambda x: float(x[1:]) if isinstance(x, str) else x)
    dataframe['Market Cap ($M USD)'] = dataframe['Market Cap ($M USD)'].apply(
        lambda x: float(x[1:].replace(',', '')) if isinstance(x, str) else x)
    dataframe['Market Cap Category'] = dataframe['Market Cap ($M USD)'].apply(
        lambda x: "Small" if x < 2000 else "Medium" if x <= 10000 else "Large")
    # Returning the Dataframe
    return dataframe


# Function to create the portfolio dataframe
def create_portfolio(initial_dataframe):
    portfolio = pd.DataFrame(index=initial_dataframe.index)
    portfolio['Sector'] = initial_dataframe['Sector']
    portfolio['Market Cap'] = initial_dataframe['Market Cap Category']
    portfolio['Allocation'] = 1 / len(initial_dataframe)
    portfolio['Value'] = portfolio['Allocation'] * 100000
    portfolio['Sell Value'] = None
    portfolio['Overdraft'] = 0
    portfolio['Total Amount'] = portfolio['Value']
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
    portfolio['Investment'] = portfolio['Value']
    portfolio['Unrealized ROI'] = ((portfolio['Value'] / portfolio['Investment']) - 1) * 100
    portfolio['Materialized ROI'] = None
    portfolio['Combined ROI'] = portfolio[['Materialized ROI', 'Unrealized ROI']].sum(axis=1)
    portfolio['Days Holding'] = 0
    ROI = portfolio.pop('Combined ROI')
    portfolio.insert(0, 'Combined ROI', ROI)
    Holding = portfolio.pop('Days Holding')
    portfolio.insert(0, 'Days Holding', Holding)

    return portfolio


def get_ipo_date(ticker_symbol):
    stock_data = yf.Ticker(ticker_symbol)
    history = stock_data.history(period="max").tz_localize(None)
    first_trading_date = history.index[0].date()

    return first_trading_date


def update_portfolio(portfolio_dataframe, final_dataframe):
    # Align final dataframe
    final_dataframe.reindex(portfolio_dataframe.index)

    # Update Pricing
    portfolio_dataframe['Yesterday Price'] = portfolio_dataframe['Today Price']
    portfolio_dataframe['Today Price'] = final_dataframe['Price']
    # Check if any stocks were sold
    sold = ~portfolio_dataframe.index.isin(final_dataframe.index)
    # Check if the stock is active
    active_stock = portfolio_dataframe['First Entry']
    portfolio_dataframe.loc[sold & active_stock, 'Sell Price'] = portfolio_dataframe['Yesterday Price']
    portfolio_dataframe.loc[sold & active_stock, 'Sell Value'] = portfolio_dataframe['Sell Price'] * \
                                                                 portfolio_dataframe['Quantity']
    sold_stocks(portfolio_dataframe.loc[sold & active_stock])
    portfolio_dataframe.loc[sold & active_stock, 'Quantity'] = 0
    portfolio_dataframe.loc[sold & active_stock, 'Materialized ROI'] = portfolio_dataframe['Unrealized ROI']
    portfolio_dataframe.loc[sold, 'First Entry'] = False
    portfolio_dataframe.loc[active_stock, 'Days Holding'] += 1
    # Update Daily Count
    rebought = (~sold) & (portfolio_dataframe['Quantity'] == 0)
    portfolio_dataframe = portfolio_dataframe[~rebought]
    portfolio_dataframe.loc[rebought, 'Materialized ROI'] = None
    portfolio_dataframe.loc[~portfolio_dataframe['Second Entry'] & active_stock, 'Days Since First Entry'] += 1
    portfolio_dataframe.loc[
        (portfolio_dataframe['Second Entry']) & (~portfolio_dataframe['Third Entry']), 'Days Since Second Entry'] += 1

    # Second Entry Action
    second_entry = (~portfolio_dataframe['Second Entry']) & ((portfolio_dataframe['Days Since First Entry'] == 90) | (
            portfolio_dataframe['Today Price'] > portfolio_dataframe['First Entry Price'] * 1.2))
    portfolio_dataframe.loc[second_entry, 'Second Entry'] = True
    portfolio_dataframe.loc[second_entry, 'Second Entry Price'] = portfolio_dataframe['Today Price']
    portfolio_dataframe.loc[second_entry, 'Investment'] += 1500
    portfolio_dataframe.loc[second_entry, 'Quantity'] += 1500 / portfolio_dataframe['Second Entry Price']
    # Third Entry Action
    third_entry = (portfolio_dataframe['Second Entry']) & (~portfolio_dataframe['Third Entry']) & (
            (portfolio_dataframe['Days Since Second Entry'] == 90) | (
            portfolio_dataframe['Today Price'] > portfolio_dataframe['Second Entry Price'] * 1.2))
    portfolio_dataframe.loc[third_entry, 'Third Entry'] = True
    portfolio_dataframe.loc[third_entry, 'Third Entry Price'] = portfolio_dataframe['Today Price']
    portfolio_dataframe.loc[third_entry, 'Investment'] += 1500
    portfolio_dataframe.loc[third_entry, 'Quantity'] += 1500 / portfolio_dataframe['Third Entry Price']
    # Update Allocation and Value
    portfolio_dataframe['Total Amount'] = portfolio_dataframe['Quantity'] * portfolio_dataframe['Today Price']
    portfolio_dataframe['Allocation'] = portfolio_dataframe['Total Amount'] / portfolio_dataframe['Total Amount'].sum()

    portfolio_dataframe['Unrealized ROI'] = (portfolio_dataframe['Total Amount'] / portfolio_dataframe[
        'Investment'] - 1) * 100
    portfolio_dataframe['Combined ROI'] = (portfolio_dataframe[['Materialized ROI', 'Unrealized ROI']].sum(axis=1))
    # Add new stocks that were not in the portfolio before
    new_stocks = final_dataframe.index.difference(portfolio_dataframe.index)
    if not new_stocks.empty:
        new_rows = pd.DataFrame(index=new_stocks)
        new_rows['Sector'] = final_dataframe.loc[new_stocks, 'Sector']
        new_rows['Market Cap'] = final_dataframe.loc[new_stocks, 'Market Cap Category']
        new_rows['Allocation'] = 0.02
        new_rows['Value'] = new_rows['Allocation'] * 100000
        new_rows['Overdraft'] = 0
        new_rows['Sell Value'] = None
        new_rows['Total Amount'] = new_rows['Value']
        new_rows['Yesterday Price'] = None
        new_rows['Today Price'] = final_dataframe.loc[new_stocks, 'Price']
        new_rows['Sell Price'] = None
        new_rows['First Entry'] = True
        new_rows['First Entry Price'] = final_dataframe.loc[new_stocks, 'Price']
        new_rows['Days Since First Entry'] = 0
        new_rows['Second Entry'] = False
        new_rows['Second Entry Price'] = None
        new_rows['Days Since Second Entry'] = 0
        new_rows['Third Entry'] = False
        new_rows['Third Entry Price'] = None
        new_rows['Quantity'] = new_rows['Value'] / new_rows['First Entry Price']
        new_rows['Investment'] = new_rows['Value']
        new_rows['Unrealized ROI'] = ((new_rows['Value'] / new_rows['Investment']) - 1) * 100
        new_rows['Materialized ROI'] = None
        new_rows['Combined ROI'] = new_rows[['Materialized ROI', 'Unrealized ROI']].sum(axis=1)
        new_rows['Days Holding'] = 0
        ROI = new_rows.pop('Combined ROI')
        new_rows.insert(0, 'Combined ROI', ROI)
        Holding = new_rows.pop('Days Holding')
        new_rows.insert(0, 'Days Holding', Holding)
        bought_stocks(new_rows)

        # Add new rows to the portfolio dataframe
        portfolio_dataframe = pd.concat([portfolio_dataframe, new_rows])

    # Calculating the Overdraft
    if portfolio_dataframe['Total Amount'].sum() > 100000:
        scaling_factor = 100000 / portfolio_dataframe['Total Amount'].sum()
        portfolio_dataframe['Value'] = portfolio_dataframe['Total Amount'] * scaling_factor
        portfolio_dataframe['Overdraft'] = portfolio_dataframe['Total Amount'] - portfolio_dataframe['Value']
    else:
        portfolio_dataframe['Value'] = portfolio_dataframe['Total Amount']
        portfolio_dataframe['Overdraft'] = 0

    return portfolio_dataframe


def create_returns(portfolio_dataframe):
    # Getting the tickers
    tickers = portfolio_dataframe.index.tolist()
    # To get the largest time period possible in which all stocks were traded, we will get the latest IPO
    latest_ipo = max([get_ipo_date(ticker) for ticker in portfolio_dataframe.index.tolist()])
    # Creating the Stock Returns Dataframe
    data = yf.download(tickers, start=latest_ipo)
    # Extract the 'Close' prices
    close_prices = data['Close']
    # Transpose the DataFrame so that tickers are the index and dates are columns
    returns = close_prices.T

    return returns


def create_mean_cumulative_returns(portfolio_dataframe):
    # Getting the tickers
    tickers = portfolio_dataframe.index.tolist()

    # To get the largest time period possible in which all stocks were traded, get the latest IPO
    latest_ipo = max([get_ipo_date(ticker) for ticker in tickers])

    # Download stock data starting from the latest IPO date
    data = yf.download(tickers, start=latest_ipo)

    # Extract the 'Close' prices
    close_prices = data['Close']

    # Calculate daily returns (percentage change in closing prices)
    daily_returns = close_prices.pct_change().dropna()

    # Calculate cumulative returns of the portfolio
    cumulative_returns = (1 + daily_returns).cumprod() - 1

    # Calculate the mean cumulative returns for all stocks in the portfolio
    mean_cumulative_returns = cumulative_returns.mean(axis=1)

    # Download index data
    indexes = ['^GSPC', '^IXIC', '^DJI']
    data_indexes = yf.download(indexes, start=latest_ipo)

    # Extract 'Close' prices for indexes
    close_prices_indexes = data_indexes['Close']

    # Calculate daily returns for indexes
    daily_returns_indexes = close_prices_indexes.pct_change().dropna()

    # Calculate cumulative returns for indexes
    cumulative_returns_indexes = (1 + daily_returns_indexes).cumprod() - 1

    # Combine cumulative returns of portfolio and indexes
    mean_cumulative_returns.name = "Portfolio"
    total_cumulative_returns = pd.concat([mean_cumulative_returns, cumulative_returns_indexes], axis=1)

    # Rename index columns
    total_cumulative_returns = total_cumulative_returns.rename(
        columns={"^DJI": "Dow Jones", "^IXIC": "NASDAQ", "^GSPC": "S&P 500"}
    )

    # Ensure 'Date' is the index name for Streamlit plotting
    total_cumulative_returns.index = total_cumulative_returns.index.date
    total_cumulative_returns.index.name = 'Date'

    return total_cumulative_returns
