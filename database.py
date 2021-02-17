import config.config as config
# Import database module.
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


class Database(object):
    db = None
    ref = None

    @staticmethod
    def initialize(bucket_name):
        print('init db + {}'.format(bucket_name) )
        # Fetch the service account key JSON file contents
        cred = credentials.Certificate(config.CREDENTIALS_FILE_FIREBASE)

        # Initialize the app with a service account, granting admin privileges
        firebase_admin.initialize_app(cred, {'databaseURL': 'https://schc-sigfox-upc-default-rtdb.firebaseio.com/'})

        # Get a database reference to our database.
        Database.ref = db.reference()

    @staticmethod
    def save(bucket_name, blob_text, destination_blob_name):
        print("[DATABASE]: saving in {}".format(bucket_name + "/" + destination_blob_name))
        data_ref = Database.ref.child(bucket_name + "/" + destination_blob_name)
        data_ref.set(blob_text)

    @staticmethod
    def read(bucket_name, blob_name):
        print("[DATABASE]: reading from {}".format(bucket_name + "/" + blob_name))
        data_ref = Database.ref.child(bucket_name + "/" + blob_name)
        return data_ref.get()

    @staticmethod
    def delete(bucket_name, blob_name):
        print("[DATABASE]: deleting from {}".format(bucket_name + "/" + blob_name))
        data_ref = Database.ref.child(bucket_name + "/" + blob_name)
        return data_ref.delete()

    @staticmethod
    def delete_all(bucket_name):
        print("[DATABASE]: deleting from {}".format(bucket_name))
        data_ref = Database.ref.child(bucket_name)
        return data_ref.delete()
