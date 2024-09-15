import streamlit as st
import pandas as pd


def generate_tables(stock_dataframe):
    # Criação de um DataFrame vazio
    growth_data = []

    for ticker in stock_dataframe.columns[1:]:
        first_price = stock_dataframe[ticker].iloc[0]
        last_price = stock_dataframe[ticker].iloc[-1]

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
