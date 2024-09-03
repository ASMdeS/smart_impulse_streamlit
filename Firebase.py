import firebase_admin
from firebase_admin import credentials, storage
import streamlit as st

# Load Firebase credentials (assuming you're using Streamlit's secrets management)
firebase_credentials = dict(st.secrets["firebase"]['my_project_settings'])

# Initialize the Firebase Admin SDK
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'smt-bot-staging'
})

# Specify the folder path based on the URL
folder_path = 'smt_momentum_daily'

# Access the Storage bucket
bucket = storage.bucket()

# List all files in the specified folder
blobs = list(bucket.list_blobs(prefix=folder_path))

# Sort the files by the 'updated' attribute to get the latest one
blobs.sort(key=lambda x: x.updated, reverse=True)

# Get the latest file
latest_blob = blobs[0]

# Specify where to download the file locally
local_path = 'data/latest_file.xlsx'

# Download the latest file
latest_blob.download_to_filename(local_path)

print(f'Latest file downloaded to {local_path}')
