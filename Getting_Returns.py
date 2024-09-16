import yfinance as yf
import pandas as pd


def get_ipo_date(ticker_symbol):
    stock_data = yf.Ticker(ticker_symbol)
    history = stock_data.history(period="max").tz_localize(None)
    first_trading_date = history.index[0].date()

    return first_trading_date


def create_mean_cumulative_returns(portfolio_dataframe):
    # Getting the tickers
    tickers = portfolio_dataframe.index.tolist()
    unique_tickers = list(set([ticker.split('.')[0] for ticker in tickers]))

    # To get the largest time period possible in which all stocks were traded, get the latest IPO
    latest_ipo = max([get_ipo_date(ticker) for ticker in unique_tickers])

    # Download stock data starting from the latest IPO date
    data = yf.download(unique_tickers, start=latest_ipo)

    # Extract the 'Close' prices
    close_prices = data['Close']

    # Transpose the DataFrame so that tickers are the index and dates are columns
    returns = close_prices.T

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

    return returns, total_cumulative_returns
