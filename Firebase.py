import os
import firebase_admin
from firebase_admin import credentials, storage
import streamlit as st
import Creating_Portfolio
import pandas as pd

# Cache the Firebase initialization to avoid multiple initializations
@st.cache_resource
def init_firebase():
    firebase_credentials = dict(st.secrets["firebase"]['my_project_settings'])
    cred = credentials.Certificate(firebase_credentials)
    # Initialize the Firebase Admin SDK (cached)
    return firebase_admin.initialize_app(cred, {
        'storageBucket': 'smt-bot-staging'
    })

# Initialize Firebase
firebase_app = init_firebase()

# Access the Storage bucket
bucket = storage.bucket()

# Folder and local paths
folder_path = 'smart_impulse'
data_dir = 'data'
csv_file_path = os.path.join(data_dir, 'smart_portfolio.csv')

# Ensure the 'data' directory exists
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Check if the smart portfolio CSV already exists
if os.path.exists(csv_file_path):
    # Load the existing portfolio from CSV
    smart_portfolio = pd.read_csv(csv_file_path, index_col=0)
    porfolio_created = True
    print("Smart portfolio loaded from CSV.")
else:
    smart_portfolio = pd.DataFrame()  # Start with an empty DataFrame
    porfolio_created = False

# List all files in the specified folder in Firebase Storage
blobs = list(bucket.list_blobs(prefix=folder_path))

# Get the list of files already downloaded in the "data" directory
local_files = os.listdir(data_dir)

# Download files not in the "data" directory
for blob in blobs:
    original_filename = os.path.basename(blob.name)

    if original_filename:  # Skip directories or empty filenames
        new_filename = original_filename[-15:]

        # Download only if the file does not exist locally
        if new_filename not in local_files:
            local_path = os.path.join(data_dir, new_filename)
            blob.download_to_filename(local_path)
            print(f'File downloaded to {local_path}')
            new_dataframe = Creating_Portfolio.excel_to_dataframe(local_path)

            # Create or update the portfolio
            if smart_portfolio.empty:
                smart_portfolio = Creating_Portfolio.create_portfolio(new_dataframe)
            else:
                smart_portfolio = Creating_Portfolio.update_portfolio(smart_portfolio, new_dataframe)

            # Save the portfolio to CSV after every update
            smart_portfolio.to_csv(csv_file_path)
            print(f'Smart portfolio updated and saved to {csv_file_path}')
            local_files = os.listdir(data_dir)

print('All missing files have been downloaded.')

# Generate returns and cumulative returns
smart_returns = Creating_Portfolio.create_returns(smart_portfolio)
smart_cumulative_returns = Creating_Portfolio.create_mean_cumulative_returns(smart_portfolio)
