from google.cloud import storage


# ====== CLOUD STORAGE FUNCTIONS ======


def upload_blob(bucket_name, blob_text, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    if type(blob_text) == bytes or type(blob_text) == bytearray:
        blob_text = blob_text.encode()
    blob.upload_from_string(str(blob_text))
    print(f'[BHF] File uploaded to {destination_blob_name}.')


def read_blob(bucket_name, blob_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    return blob.download_as_string().decode('utf-8') if blob else None


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
    print(f'[BHF] Folder uploaded to {folder_name}.')


def delete_blob(bucket_name, blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    if blob is not None:
        blob.delete()
        print(f"[BHF] Deleted blob {blob_name}")
    else:
        print(f"[BHF] {blob_name} doesn't exist.")


def initialize_blobs(bucket_name, profile):
    if not exists_blob(bucket_name, "all_windows/"):
        print("[BHF] Initializing... (be patient)")
        create_folder(bucket_name, "all_windows/")

        # For each window in the SCHC Profile, create its blob.
        for i in range(2 ** profile.M):
            create_folder(bucket_name, f"all_windows/window_{i}/")

            # For each fragment in the SCHC Profile, create its blob.
            for j in range(2 ** profile.N - 1):
                upload_blob(bucket_name, "", f"all_windows/window_{i}/fragment_{i}_{j}")

            # Create the blob for each bitmap.
            upload_blob(bucket_name, "0" * profile.BITMAP_SIZE, f"all_windows/window_{i}/bitmap_{i}")

        print("[BHF] BLOBs created")
