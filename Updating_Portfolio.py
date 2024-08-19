# Importing the Dataframes
from Creating_Portfolio import first_day, second_day, third_day, fourth_day, smart_portfolio, smart_returns

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
    # Update Daily Count
    portfolio_dataframe.loc[~portfolio_dataframe['Second Entry'], 'Days Since First Entry'] += 1
    portfolio_dataframe.loc[(portfolio_dataframe['Second Entry']) & (~portfolio_dataframe['Third Entry']), 'Days Since Second Entry'] += 1
    # Add new stocks that were not in the portfolio before
    new_stocks = final_dataframe.index.difference(portfolio_dataframe.index)
    if not new_stocks.empty:
        new_rows = pd.DataFrame(index=new_stocks)
        portfolio_dataframe['Sector'] = final_dataframe['Sector']
        new_rows['Allocation'] = 0.02
        new_rows['Value'] = portfolio_dataframe['Allocation'] * 100000
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

        # Add new rows to the portfolio dataframe
        portfolio_dataframe = pd.concat([portfolio_dataframe, new_rows])

    # Second Entry Action
    second_entry = (~portfolio_dataframe['Second Entry']) & ((portfolio_dataframe['Days Since First Entry'] == 90) | (portfolio_dataframe['Today Price'] > portfolio_dataframe['First Entry Price'] * 1.2))
    portfolio_dataframe.loc[second_entry, 'Second Entry'] = True
    portfolio_dataframe.loc[second_entry, 'Second Entry Price'] = portfolio_dataframe
    portfolio_dataframe.loc[second_entry, 'Quantity'] *= 1.015
    # Third Entry Action
    third_entry = (portfolio_dataframe['Second Entry']) & (~portfolio_dataframe['Third Entry']) & ((portfolio_dataframe['Days Since Second Entry'] == 90) | (portfolio_dataframe['Today Price'] > portfolio_dataframe['Second Entry Price'] * 1.2))
    portfolio_dataframe.loc[third_entry, 'Third Entry'] = True
    portfolio_dataframe.loc[third_entry, 'Third Entry Price'] = portfolio_dataframe['Today Price']
    portfolio_dataframe.loc[third_entry, 'Quantity'] *= 1.015
    # Update Allocation and Value
    portfolio_dataframe['Value'] = portfolio_dataframe['Quantity'] * portfolio_dataframe['Today Price']
    portfolio_dataframe['Allocation'] = portfolio_dataframe['Value'] / portfolio_dataframe['Value'].sum()
    # Calculating the overdraft
    if portfolio_dataframe['Value'].sum() > 100000:
        scaling_factor = 100000 / portfolio_dataframe['Value'].sum()
        portfolio_dataframe['Value'] = portfolio_dataframe['Value'] * scaling_factor
        portfolio_dataframe['Overdraft'] = portfolio_dataframe['Value'] * (1 - scaling_factor)

    # Creating the Stock Returns Dataframe
    data = yf.download(portfolio_dataframe.index.tolist(), start="2022-01-01", end="2023-01-01")
    # Extract the 'Close' prices
    close_prices = data['Close']
    # Transpose the DataFrame so that tickers are the index and dates are columns
    returns = close_prices.T

    return portfolio_dataframe, returns


second_portfolio, second_returns = update_portfolio(smart_portfolio, second_day)


third_portfolio, third_returns = update_portfolio(second_portfolio, third_day)
