import threading

from google.cloud import storage
import json


def upload_blob_using_threads(bucket_name, blob_text, destination_blob_name):
    print("[BLOB]: Uploading with threads...")
    thread = threading.Thread(target=upload_blob, args=(bucket_name, blob_text, destination_blob_name))
    thread.start()


def upload_blob(bucket_name, blob_text, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    if type(blob_text) == bytes or type(blob_text) == bytearray:
        blob_text = blob_text.encode()
    blob.upload_from_string(str(blob_text))
    print('[BLOB]: File uploaded to {}.'.format(destination_blob_name))


def read_blob(bucket_name, blob_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    return blob.download_as_string().decode('utf-8') if blob else None


def delete_blob(bucket_name, blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    blob.delete()


def exists_blob(bucket_name, blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.exists()


def create_folder(bucket_name, folder_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(folder_name)
    blob.upload_from_string("")
    print('[BLOB]: Folder uploaded to {}.'.format(folder_name))


def size_blob(bucket_name, blob_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    return blob.size if blob else 0


def send_ack(request, ack):
    device = request["device"]
    print("ack string -> {}".format(ack.to_string()))
    response_dict = {device: {'downlinkData': ack.to_bytes().hex()}}
    response_json = json.dumps(response_dict)
    print("response_json -> {}".format(response_json))
    return response_json
