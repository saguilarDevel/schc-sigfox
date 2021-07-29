# Configuration variables for SCHCFOX
# Change the variables name to your files, then remove track from git
# git rm --cached config/config.py

# Cloud Storage Bucket Name
BUCKET_NAME = 'wyschc-2021'
#
CLIENT_SECRETS_FILE = './credentials/certain-perigee-321314-4728dbdf47cd.json'

# File where we will store authentication credentials after acquiring them.
CREDENTIALS_FILE = './credentials/certain-perigee-321314-4728dbdf47cd.json'

CREDENTIALS_FILE_FIREBASE = './credentials/wyschc27-firebase-adminsdk-oq835-1a99029948.json'
FIREBASE_RTDB_URL = 'https://wyschc27-default-rtdb.firebaseio.com/'

CLEAN_URL = 'https://southamerica-east1-certain-perigee-321314.cloudfunctions.net/clean'
RECEIVER_URL = 'https://southamerica-east1-certain-perigee-321314.cloudfunctions.net/hello_get'
REASSEMBLE_URL = 'https://southamerica-east1-certain-perigee-321314.cloudfunctions.net/http_reassemble'
TEST_URL = 'https://southamerica-east1-certain-perigee-321314.cloudfunctions.net/test'
CLEAN_WINDOW_URL = 'https://southamerica-east1-certain-perigee-321314.cloudfunctions.net/clean_window'
