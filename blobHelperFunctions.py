import threading

from google.cloud import storage
import json


def upload_blob_using_threads(bucket_name, blob_text, destination_blob_name):
    print("Uploading with threads...")
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
    print(f'File uploaded to {destination_blob_name}.')


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
    print(f'Folder uploaded to {folder_name}.')


def size_blob(bucket_name, blob_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    return blob.size if blob else 0


def send_ack(request, ack):
    device = request["device"]
    print(f"ack string -> {ack.to_string()}")
    response_dict = {device: {'downlinkData': ack.to_bytes().hex()}}
    response_json = json.dumps(response_dict)
    print(f"response_json -> {response_json}")
    return response_json


def initialize_blobs(bucket_name, profile):
    if not exists_blob(bucket_name, "all_windows/"):
        print("INITIALIZING... (be patient)")
        create_folder(bucket_name, "all_windows/")

        # For each window in the SCHC Profile, create its blob.
        for i in range(2 ** profile.M):
            create_folder(bucket_name, f"all_windows/window_{i}/")

            # For each fragment in the SCHC Profile, create its blob.
            for j in range(2 ** profile.N - 1):
                upload_blob(bucket_name, "", f"all_windows/window_{i}/fragment_{i}_{j}")

            # Create the blob for each bitmap.
            if not exists_blob(bucket_name, f"all_windows/window_{i}/bitmap_{i}" or size_blob(bucket_name,
                                                                                              f"all_windows/"
                                                                                              f"window_{i}/"
                                                                                              f"bitmap_{i}") == 0):
                bitmap = ""
                for b in range(profile.BITMAP_SIZE):
                    bitmap += "0"
                upload_blob(bucket_name, bitmap, f"all_windows/window_{i}/bitmap_{i}")

        print("BLOBs created")
