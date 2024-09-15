import telegram
import asyncio
import streamlit as st


def send_message(message):
    bot_token = st.secrets["telegram"]["bot_token"]
    bot = telegram.Bot(token=bot_token)
    chat_id = st.secrets["telegram"]["chat_id"]
    message_to_send = message
    asyncio.run(bot.send_message(chat_id=chat_id, text=message_to_send))

    print("Message sent!")


def sold_stocks(dataframe):
    batch_messages = []
    for index, row in dataframe.iterrows():
        message = f'{row["Quantity"]:.2f} of {index} sold at {row["Today Price"]:.2f}'
        batch_messages.append(message)
    single_message = '\n'.join(batch_messages)
    send_message(single_message)


def bought_stocks(dataframe):
    batch_messages = []
    for index, row in dataframe.iterrows():
        message = f'{row["Quantity"]:.2f} of {index} bought at {row["Today Price"]:.2f}'
        batch_messages.append(message)
    single_message = '\n'.join(batch_messages)
    send_message(single_message)
