import os
import firebase_admin
from firebase_admin import credentials, storage
import streamlit as st
import Creating_Portfolio

# Load Firebase credentials (assuming you're using Streamlit's secrets management)
firebase_credentials = dict(st.secrets["firebase"]['my_project_settings'])

# Initialize the Firebase Admin SDK
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'smt-bot-staging'
})

# Specify the folder path based on the URL
folder_path = 'smt_momentum_daily'

# Ensure the 'data' directory exists
data_dir = 'data'
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Access the Storage bucket
bucket = storage.bucket()

# List all files in the specified folder in Firebase Storage
blobs = list(bucket.list_blobs(prefix=folder_path))

print(blobs)

# Get the list of files already downloaded in the "data" directory
local_files = os.listdir(data_dir)

# Download files not in the "data" directory
for blob in blobs:
    # Get the filename
    filename = os.path.basename(blob.name)

    # Ensure that the blob has a valid filename (skip directories and empty filenames)
    if filename:
        # Check if the file is already downloaded
        if filename not in local_files:
            # Specify the local path for the file
            local_path = os.path.join(data_dir, filename)

            # Download the file
            blob.download_to_filename(local_path)
            print(f'File downloaded to {local_path}')
            if


print('All missing files have been downloaded.')

