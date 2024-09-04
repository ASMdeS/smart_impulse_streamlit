# Importing the Dataframes
from Creating_Portfolio import get_ipo_date, first_day, second_day, third_day, smart_portfolio

import pandas as pd
import yfinance as yf


def update_portfolio(portfolio_dataframe, final_dataframe):
    # Align final dataframe
    final_dataframe.reindex(portfolio_dataframe.index)

    # Update Pricing
    portfolio_dataframe['Yesterday Price'] = portfolio_dataframe['Today Price']
    portfolio_dataframe['Today Price'] = final_dataframe['Price']
    # Check if any stocks were sold
    sold = ~portfolio_dataframe.index.isin(final_dataframe.index)
    portfolio_dataframe.loc[sold, 'Sell Price'] = portfolio_dataframe['Yesterday Price']
    portfolio_dataframe.loc[sold, 'Quantity'] = 0
    portfolio_dataframe.loc[sold, 'First Entry'] = False
    portfolio_dataframe.loc[sold, 'Materialized ROI'] = portfolio_dataframe['Unrealized ROI']
    # Update Daily Count
    portfolio_dataframe.loc[~portfolio_dataframe['Second Entry'], 'Days Since First Entry'] += 1
    portfolio_dataframe.loc[(portfolio_dataframe['Second Entry']) & (~portfolio_dataframe['Third Entry']), 'Days Since Second Entry'] += 1
    # Add new stocks that were not in the portfolio before
    new_stocks = final_dataframe.index.difference(portfolio_dataframe.index)
    if not new_stocks.empty:
        new_rows = pd.DataFrame(index=new_stocks)
        portfolio_dataframe['Sector'] = final_dataframe['Sector']
        portfolio_dataframe['Market Category'] = final_dataframe['Market Cap Category']
        new_rows['Allocation'] = 0.02
        new_rows['Value'] = portfolio_dataframe['Allocation'] * 100000
        new_rows['Overdraft'] = 0
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
        new_rows['Combined ROI'] = 1 - new_rows[['Materialized ROI', 'Unrealized ROI']].sum(axis=1)
        new_rows['Days Holding'] = 0
        ROI = new_rows.pop('Combined ROI')
        new_rows.insert(0, 'Combined ROI', ROI)
        Holding = new_rows.pop('Days Holding')
        new_rows.insert(0, 'Days Holding', Holding)

        # Add new rows to the portfolio dataframe
        portfolio_dataframe = pd.concat([portfolio_dataframe, new_rows])

    # Second Entry Action
    second_entry = (~portfolio_dataframe['Second Entry']) & ((portfolio_dataframe['Days Since First Entry'] == 90) | (portfolio_dataframe['Today Price'] > portfolio_dataframe['First Entry Price'] * 1.2))
    portfolio_dataframe.loc[second_entry, 'Second Entry'] = True
    portfolio_dataframe.loc[second_entry, 'Second Entry Price'] = portfolio_dataframe['Today Price']
    portfolio_dataframe.loc[second_entry, 'Investment'] += 1500
    portfolio_dataframe.loc[second_entry, 'Quantity'] += 1500 / portfolio_dataframe['Second Entry Price']
    # Third Entry Action
    third_entry = (portfolio_dataframe['Second Entry']) & (~portfolio_dataframe['Third Entry']) & ((portfolio_dataframe['Days Since Second Entry'] == 90) | (portfolio_dataframe['Today Price'] > portfolio_dataframe['Second Entry Price'] * 1.2))
    portfolio_dataframe.loc[third_entry, 'Third Entry'] = True
    portfolio_dataframe.loc[third_entry, 'Third Entry Price'] = portfolio_dataframe['Today Price']
    portfolio_dataframe.loc[third_entry, 'Investment'] += 1500
    portfolio_dataframe.loc[third_entry, 'Quantity'] += 1500 / portfolio_dataframe['Third Entry Price']
    # Update Allocation and Value
    portfolio_dataframe['Total Amount'] = portfolio_dataframe['Quantity'] * portfolio_dataframe['Today Price']
    portfolio_dataframe['Allocation'] = portfolio_dataframe['Total Amount'] / portfolio_dataframe['Total Amount'].sum()
    portfolio_dataframe['Unrealized ROI'] = (portfolio_dataframe['Total Amount'] / portfolio_dataframe['Investment'] - 1) * 100
    portfolio_dataframe['Combined ROI'] = (portfolio_dataframe[['Materialized ROI', 'Unrealized ROI']].sum(axis=1))
    portfolio_dataframe['Days Holding'] += 1

    # Calculating the Overdraft
    if portfolio_dataframe['Total Amount'].sum() > 100000:
        scaling_factor = 100000 / portfolio_dataframe['Total Amount'].sum()
        portfolio_dataframe['Value'] = portfolio_dataframe['Total Amount'] * scaling_factor
        portfolio_dataframe['Overdraft'] = portfolio_dataframe['Total Amount'] - portfolio_dataframe['Value']
    else:
        portfolio_dataframe['Value'] = portfolio_dataframe['Total Amount']
        portfolio_dataframe['Overdraft'] = 0

    top_performers = portfolio_dataframe.sort_values(by='Combined ROI', ascending=False).head(10)
    top_losers = portfolio_dataframe.sort_values(by='Combined ROI', ascending=True).head(10)

    return portfolio_dataframe, top_performers, top_losers

def create_returns(portfolio_dataframe):
    #Getting the tickers
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


second_portfolio, second_performers, second_losers = update_portfolio(smart_portfolio, second_day)


third_portfolio, third_performers, third_losers = update_portfolio(second_portfolio, third_day)


third_returns = create_returns(third_portfolio)

grouped_by_cap = third_portfolio.groupby('Market Cap').sum()
