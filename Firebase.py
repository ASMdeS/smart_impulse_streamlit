import os
import firebase_admin
from firebase_admin import credentials, storage
import streamlit as st
import Creating_Portfolio
import pandas as pd

# Load Firebase credentials (assuming you're using Streamlit's secrets management)
firebase_credentials = dict(st.secrets["firebase"]['my_project_settings'])

# Initialize the Firebase Admin SDK
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'smt-bot-staging'
})

# Specify the folder path based on the URL
folder_path = 'smart_impulse'

# Ensure the 'data' directory exists
data_dir = 'data'
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# CSV file to persist the smart portfolio
csv_file_path = os.path.join(data_dir, 'smart_portfolio.csv')

# Access the Storage bucket
bucket = storage.bucket()

# List all files in the specified folder in Firebase Storage
blobs = list(bucket.list_blobs(prefix=folder_path))

# Get the list of files already downloaded in the "data" directory
local_files = os.listdir(data_dir)

# Check if the smart portfolio CSV already exists
if os.path.exists(csv_file_path):
    # Load the existing portfolio from CSV
    smart_portfolio = pd.read_csv(csv_file_path, index_col=0)
    porfolio_created = True
    print("Smart portfolio loaded from CSV.")
else:
    smart_portfolio = pd.DataFrame()  # Start with an empty DataFrame
    porfolio_created = False

# Download files not in the "data" directory
for blob in blobs:
    # Get the original filename from the blob's full path
    original_filename = os.path.basename(blob.name)

    # Ensure that the blob has a valid filename (skip directories and empty filenames)
    if original_filename:
        # Get the last 10 characters of the filename
        new_filename = original_filename[-15:]

        # Check if the file (with the new name) is already downloaded
        if new_filename not in local_files:
            # Specify the local path for the file with the new filename
            local_path = os.path.join(data_dir, new_filename)

            # Download the file
            blob.download_to_filename(local_path)
            print(f'File downloaded to {local_path}')
            new_dataframe = Creating_Portfolio.excel_to_dataframe(local_path)

            # Create or update the portfolio
            if smart_portfolio.empty:
                # If smart_portfolio is empty, initialize it with new data
                smart_portfolio = Creating_Portfolio.create_portfolio(new_dataframe)
            else:
                # If smart_portfolio already exists, update it with new data
                smart_portfolio = Creating_Portfolio.update_portfolio(smart_portfolio, new_dataframe)

            # Save the portfolio to CSV after every update
            smart_portfolio.to_csv(csv_file_path)
            print(f'Smart portfolio updated and saved to {csv_file_path}')
            local_files = os.listdir(data_dir)

print('All missing files have been downloaded.')



smart_returns = Creating_Portfolio.create_returns(smart_portfolio)

# Display the final portfolio
print(smart_portfolio)
