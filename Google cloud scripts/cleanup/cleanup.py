from google.cloud import storage


# ====== CLOUD STORAGE FUNCTIONS ======


def upload_blob(bucket_name, blob_text, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    if type(blob_text) == bytes or type(blob_text) == bytearray:
        blob_text = blob_text.encode()
    blob.upload_from_string(str(blob_text))
    print(f'[BHF] File uploaded to {destination_blob_name}.')


def delete_blob(bucket_name, blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    if blob is not None:
        blob.delete()
        print(f"[BHF] Deleted blob {blob_name}")
    else:
        print(f"[BHF] {blob_name} doesn't exist.")


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


# ====== CLASSES ======


class Protocol:
    NAME = None
    RULE_ID_SIZE = 0
    L2_WORD_SIZE = 0
    TILE_SIZE = 0
    M = 0
    N = 0
    BITMAP_SIZE = 0
    RCS_SIZE = 0
    RCS_ALGORITHM = None
    T = 0
    MAX_ACK_REQUESTS = 0
    MAX_WIND_FCN = 0
    RETRANSMISSION_TIMER_VALUE = None
    INACTIVITY_TIMER_VALUE = None
    UPLINK_MTU = 0
    DOWNLINK_MTU = 0


class Sigfox(Protocol):
    direction = None
    mode = None

    def __init__(self, direction, mode, header_bytes):

        # print("This protocol is in " + direction + " direction and " + mode + " mode.")

        self.NAME = "SIGFOX"
        self.direction = direction
        self.mode = mode
        self.RETRANSMISSION_TIMER_VALUE = 45  # (45) enough to let a downlink message to be sent if needed
        self.INACTIVITY_TIMER_VALUE = 60  # (60) for demo purposes

        self.SIGFOX_DL_TIMEOUT = 20  # This is to be tested

        self.L2_WORD_SIZE = 8  # The L2 word size used by Sigfox is 1 byte

        self.N = 0

        self.HEADER_LENGTH = 0

        self.MESSAGE_INTEGRITY_CHECK_SIZE = None  # TBD
        self.RCS_ALGORITHM = None  # TBD

        self.UPLINK_MTU = 12 * 8
        self.DOWNLINK_MTU = 8 * 8

        if direction == "UPLINK":
            # if mode == "NO ACK":
            #     self.HEADER_LENGTH = 8
            #     self.RULE_ID_SIZE = 2  # recommended
            #     self.T = 2  # recommended
            #     self.N = 4  # recommended
            #     self.M = 0

            if mode == "ACK ALWAYS":
                pass  # TBD

            if mode == "ACK ON ERROR" and header_bytes == 1:
                self.HEADER_LENGTH = 8
                self.RULE_ID_SIZE = 2
                self.T = 1
                self.N = 3
                self.M = 2  # recommended to be single
                self.WINDOW_SIZE = 2 ** self.N - 1
                self.BITMAP_SIZE = 2 ** self.N - 1  # from excel
                self.MAX_ACK_REQUESTS = 3  # SHOULD be 2
                self.MAX_WIND_FCN = 6  # SHOULD be

            if mode == "ACK ON ERROR" and header_bytes == 2:
                self.HEADER_LENGTH = 16
                self.RULE_ID_SIZE = 7
                self.T = 1
                self.N = 5
                self.M = 3  # recommended to be single
                self.WINDOW_SIZE = 2 ** self.N - 1
                self.BITMAP_SIZE = 2 ** self.N - 1  # from excel
                self.MAX_ACK_REQUESTS = 3  # SHOULD be 2
                self.MAX_WIND_FCN = 6  # SHOULD be

        if direction == "DOWNLINK":
            if mode == "NO ACK":
                self.HEADER_LENGTH = 8
                self.RULE_ID_SIZE = 2
                self.T = 1
                self.M = 2
                self.N = 3
            if mode == "ACK ALWAYS":
                self.HEADER_LENGTH = 8
                self.RULE_ID_SIZE = 2  # recommended
                self.T = 2  # recommended
                self.N = 3  # recommended
                self.M = 1  # MUST be present, recommended to be single
                self.MAX_ACK_REQUESTS = 3  # SHOULD be 2
                self.MAX_WIND_FCN = 6  # SHOULD be

            # Sigfox downlink frames have a fixed length of 8 bytes, which means
            #    that default SCHC algorithm for padding cannot be used.  Therefore,
            #    the 3 last bits of the fragmentation header are used to indicate in
            #    bytes the size of the padding.  A size of 000 means that the full
            #    ramaining frame is used to carry payload, a value of 001 indicates
            #    that the last byte contains padding, and so on.

            else:
                pass


# ====== GLOBAL VARIABLES ======


BUCKET_NAME = 'wyschc-niclabs'


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
