import telegram
import asyncio
import streamlit as st
def send_message(message):
    # Replace 'YOUR_BOT_TOKEN' with the token you got from BotFather
    bot_token = st.secrets["telegram"]["bot_token"]
    bot = telegram.Bot(token=bot_token)

    # Replace 'YOUR_CHAT_ID' with the chat ID you got from getUpdates
    chat_id = st.secrets["telegram"]["chat_id"]

    # The message you want to send
    message_to_send = message

    # Send the message asynchronously
    asyncio.run(bot.send_message(chat_id=chat_id, text=message_to_send))

    print("Message sent!")


def sold_stocks(dataframe):
    for index, row in dataframe.iterrows():
        Message = f'{row["Quantity"]:.2f} of {index} sold at {row["Sell Price"]:.2f}'
        print(Message)
        send_message(Message)


def bought_stocks(dataframe):
    for index, row in dataframe.iterrows():
        Message = f'{row["Quantity"]:.2f} of {index} bought at {row["First Entry Price"]:.2f}'
        print(Message)
        send_message(Message)