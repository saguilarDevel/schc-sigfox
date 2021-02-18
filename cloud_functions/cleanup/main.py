from localpackage.blob_helper_functions import delete_blob, upload_blob, initialize_blobs
from localpackage.classes import Sigfox

# ====== GLOBAL VARIABLES ======


BUCKET_NAME = 'wyschc-2021'


# ====== MAIN ======


def cleanup(request):
    header_bytes = request.get_json()["header_bytes"]
    profile = Sigfox("UPLINK", "ACK ON ERROR", header_bytes)

    print("[CLN] Deleting timestamp blob")
    delete_blob(BUCKET_NAME, "timestamp")

    print("[CLN] Resetting SSN")
    upload_blob(BUCKET_NAME, "{}", "SSN")

    print("[CLN] Initializing fragments...")
    delete_blob(BUCKET_NAME, "all_windows/")
    initialize_blobs(BUCKET_NAME, profile)

    return '', 204
