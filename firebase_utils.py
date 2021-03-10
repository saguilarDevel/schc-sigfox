import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("credentials/wyschc-303621-firebase-adminsdk-4w95k-c5e83feeca.json")
firebase_admin.initialize_app(cred)
