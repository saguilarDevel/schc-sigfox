# Configuration variables for SCHCFOX
# Change the variables name to your files, then remove track from git
# git rm --cached config/config.py

# Cloud Storage Bucket Name
BUCKET_NAME = 'wyschc-2021'
#
CLIENT_SECRETS_FILE = './credentials/wyschc27-cc31b2bc6fbc.json'

# File where we will store authentication credentials after acquiring them.
CREDENTIALS_FILE = './credentials/wyschc27-cc31b2bc6fbc.json'

CREDENTIALS_FILE_FIREBASE = './credentials/wyschc27-firebase-adminsdk-oq835-1a99029948.json'
FIREBASE_RTDB_URL = 'https://wyschc27-default-rtdb.firebaseio.com/'

# Endpoints in GCP
CLEAN_URL = 'https://southamerica-east1-wyschc27.cloudfunctions.net/clean'
RECEIVER_URL = 'https://southamerica-east1-wyschc27.cloudfunctions.net/hello_get'
REASSEMBLE_URL = 'https://southamerica-east1-wyschc27.cloudfunctions.net/http_reassemble'
TEST_URL = 'https://southamerica-east1-wyschc27.cloudfunctions.net/test'
CLEAN_WINDOW_URL = 'https://southamerica-east1-wyschc27.cloudfunctions.net/clean_window'

# Local endpoints for offline testing
LOCAL_CLEAN_URL = 'http://localhost:5000/clean'
LOCAL_RECEIVER_URL = 'http://localhost:5000/receiver'
LOCAL_REASSEMBLE_URL = 'http://localhost:5000/http_reassemble'
LOCAL_TEST_URL = 'http://localhost:5000/test'
LOCAL_CLEAN_WINDOW_URL = 'http://localhost:5000/clean_window'

# Local variables:
FILENAME = ''