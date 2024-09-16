import pandas as pd
from Telegram_Bot import sold_stocks, bought_stocks


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
def create_portfolio(initial_dataframe, allocation, date):
    portfolio = pd.DataFrame(index=initial_dataframe.index)
    portfolio['Sector'] = initial_dataframe['Sector']
    portfolio['Market Cap'] = initial_dataframe['Market Cap Category']
    portfolio['Allocation'] = allocation
    portfolio['Value'] = portfolio['Allocation'] * 100000
    portfolio['Overdraft'] = 0
    portfolio['Total Amount'] = portfolio['Value']
    portfolio['Yesterday Price'] = None
    portfolio['Today Price'] = initial_dataframe['Price']
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
    portfolio['ROI'] = ((portfolio['Value'] / portfolio['Investment']) - 1) * 100
    portfolio['Days Holding'] = 0
    portfolio['Buy Date'] = date
    portfolio['Sell Date'] = None
    ROI = portfolio.pop('ROI')
    portfolio.insert(0, 'ROI', ROI)
    Holding = portfolio.pop('Days Holding')
    portfolio.insert(0, 'Days Holding', Holding)

    return portfolio


def update_portfolio(portfolio_dataframe, final_dataframe, date):
    # Align final dataframe
    final_dataframe.reindex(portfolio_dataframe.index)
    sold = ~portfolio_dataframe.index.isin(final_dataframe.index)
    portfolio_dataframe.loc[sold & portfolio_dataframe['Sell Date'].isnull(), 'Sell Date'] = date
    sold_today = portfolio_dataframe['Sell Date'] == date
    # Send Telegram message if there are sold stocks
    if not portfolio_dataframe.loc[sold_today].empty:
        sold_stocks(portfolio_dataframe.loc[sold_today])
    for stock_name in portfolio_dataframe.loc[sold_today].index:
        base_name = stock_name.split('.')[0]
        count = 1
        new_name = f"{base_name}.{count}"
        while new_name in portfolio_dataframe.index:
            count += 1
            new_name = f"{base_name}.{count}"
        portfolio_dataframe.rename(index={stock_name: new_name}, inplace=True)
    sold = pd.Series(sold, index=portfolio_dataframe.index)
    sold_dataframe = portfolio_dataframe[sold]

    portfolio_dataframe = portfolio_dataframe[~sold]
    # Update Pricing
    portfolio_dataframe['Yesterday Price'] = portfolio_dataframe['Today Price']
    portfolio_dataframe['Today Price'] = final_dataframe['Price']
    # Check if any stocks were sold
    portfolio_dataframe['Days Holding'] += 1
    # Update Daily Count
    portfolio_dataframe.loc[~portfolio_dataframe['Second Entry'], 'Days Since First Entry'] += 1
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

    portfolio_dataframe['ROI'] = (portfolio_dataframe['Total Amount'] / portfolio_dataframe[
        'Investment'] - 1) * 100
    # Add new stocks that were not in the portfolio before
    new_stocks = final_dataframe.index.difference(portfolio_dataframe.index)
    if not new_stocks.empty:
        # Create portfolio dataframe based on the new stocks
        new_rows = create_portfolio(final_dataframe.loc[new_stocks], 0.02, date)
        # Send Telegram message with the new stocks
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

    portfolio_dataframe = pd.concat([portfolio_dataframe, sold_dataframe])

    return portfolio_dataframe
