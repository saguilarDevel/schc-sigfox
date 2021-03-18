# Configuration variables for SCHCFOX
# Change the variables name to your files, then remove track from git
# git rm --cached config/config.py

# Cloud Storage Bucket Name
BUCKET_NAME = 'wyschc-2021'

# File where we will store authentication credentials after acquiring them.
CLIENT_SECRETS_FILE = './credentials/wyschc27-cc31b2bc6fbc.json'
CREDENTIALS_FILE_FIREBASE = './credentials/schc-sigfox-upc-firebase-adminsdk-jf71b-66d927162a.json'

FIREBASE_RTDB_URL = 'https://schc-sigfox-upc-default-rtdb.firebaseio.com/'

# Loss mask path
LOSS_MASK = './loss_masks/loss_mask_0.txt'
LOSS_MASK_MODIFIED = './loss_masks/loss_mask_modified.txt'

# Message to be fragmented
MESSAGE = './comm/example_300.txt'
PAYLOAD = './comm/PAYLOAD.txt'

# GCP Cloud Functions URL
SCHC_POST_URL = "https://southamerica-east1-wyschc-303621.cloudfunctions.net/schc_receiver"
REASSEMBLER_URL = "https://southamerica-east1-wyschc-303621.cloudfunctions.net/reassemble"
CLEANUP_URL = "https://southamerica-east1-wyschc-303621.cloudfunctions.net/cleanup"
