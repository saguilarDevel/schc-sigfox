import requests

from localpackage.blob_helper_functions import read_blob, upload_blob
from localpackage.classes import Sigfox, Reassembler

# ====== GLOBAL VARIABLES ======


BUCKET_NAME = 'wyschc-niclabs'
CLEANUP_URL = "https://us-central1-wyschc-niclabs.cloudfunctions.net/cleanup"


# ====== MAIN ======


def reassemble(request):
    if request.method == "POST":
        print("[RSMB] The reassembler has been launched.")
        # Get request JSON.
        request_dict = request.get_json()
        print(f'[RSMB] Received HTTP message: {request_dict}')

        current_window = int(request_dict["current_window"])
        last_index = int(request_dict["last_index"])
        header_bytes = int(request_dict["header_bytes"])

        # Initialize SCHC variables.
        profile_uplink = Sigfox("UPLINK", "ACK ON ERROR", header_bytes)
        n = profile_uplink.N

        print("[RSMB] Loading fragments")

        # Get all the fragments into an array in the format "fragment = [header, payload]"
        fragments = []

        # For each window, load every fragment into the fragments array
        for i in range(current_window + 1):
            for j in range(2 ** n - 1):
                print(f"[RSMB] Loading fragment {j}")
                fragment_file = read_blob(BUCKET_NAME, f"all_windows/window_{i}/fragment_{i}_{j}")
                print(f"[RSMB] Fragment data: {fragment_file}")
                header = fragment_file[:header_bytes]
                payload = fragment_file[header_bytes:]
                fragment = [header.encode(), payload.encode()]
                fragments.append(fragment)
                if i == current_window and j == last_index:
                    break

        # Instantiate a Reassembler and start reassembling.
        print("[RSMB] Reassembling")
        reassembler = Reassembler(profile_uplink, fragments)
        payload = bytearray(reassembler.reassemble()).decode("utf-8")

        print("[RSMB] Uploading result")
        # Upload the full message.
        upload_blob(BUCKET_NAME, payload, "PAYLOAD")

        try:
            _ = requests.post(url=CLEANUP_URL,
                              json={"header_bytes": header_bytes},
                              timeout=0.1)
        except requests.exceptions.ReadTimeout:
            pass

        return '', 204
