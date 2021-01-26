import random
import re

import requests
from flask import request
from flask import abort

# import config.config as config
# from Entities.Reassembler import Reassembler
# from Entities.Sigfox import Sigfox
# from Messages.ACK import ACK
# from Messages.Fragment import Fragment
# from Messages.ReceiverAbort import ReceiverAbort
# from blobHelperFunctions import *


# Configuration variables from config.py
# Change the variables name to your files, then remove track from git
# git rm --cached config/config.py

# Cloud Storage Bucket Name
BUCKET_NAME = 'wyschc-niclabs'
#
CLIENT_SECRETS_FILE = './credentials/WySCHC-Niclabs-7a6d6ab0ca2b.json'

# File where we will store authentication credentials after acquiring them.
CREDENTIALS_FILE = './credentials/WySCHC-Niclabs-7a6d6ab0ca2b.json'

# Loss mask path
LOSS_MASK = './loss_masks/loss_mask_0.txt'
LOSS_MASK_MODIFIED = './loss_masks/loss_mask_modified.txt'

# Message to be fragmented
MESSAGE = './comm/example_300.txt'
PAYLOAD = './comm/PAYLOAD.txt'

# Blob helper functions
import os
import threading

from google.cloud import storage
import json


def upload_blob_using_threads(bucket_name, blob_text, destination_blob_name):
    print("[BHF] Uploading with threads...")
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
    print(f'[BHF] File uploaded to {destination_blob_name}.')


def read_blob(bucket_name, blob_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    return blob.download_as_string().decode('utf-8') if blob else None


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


def size_blob(bucket_name, blob_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    return blob.size if blob else 0


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


#  FUNCTIONS
def zfill(string, width):
    if len(string) < width:
        return ("0" * (width - len(string))) + string
    else:
        return string


def insert_index(ls, pos, elmt):
    while len(ls) < pos:
        ls.append([])
    ls.insert(pos, elmt)


def replace_bit(string, position, value):
    return '%s%s%s' % (string[:position], value, string[position + 1:])


def find(string, character):
    return [i for i, ltr in enumerate(string) if ltr == character]


def bitstring_to_bytes(s):
    return int(s, 2).to_bytes(len(s) // 8, byteorder='big')


def is_monochar(s):
    return len(set(s)) == 1


def send_ack(request, ack):
    device = request["device"]
    print(f"ack string -> {ack.to_string()}")
    response_dict = {device: {'downlinkData': ack.to_bytes().hex()}}
    response_json = json.dumps(response_dict)
    print(f"response_json -> {response_json}")
    return response_json


# ACK
class ACK:
    profile = None
    rule_id = None
    dtag = None
    w = None
    bitmap = None
    c = None
    header = ''
    padding = ''

    window_number = None

    def __init__(self, profile, rule_id, dtag, w, c, bitmap, padding=''):
        self.profile = profile
        self.rule_id = rule_id
        self.dtag = dtag
        self.w = w
        self.c = c
        self.bitmap = bitmap
        self.padding = padding

        # Bitmap may or may not be carried
        self.header = self.rule_id + self.dtag + self.w + self.c + self.bitmap
        print(f"header {self.header}")
        while len(self.header + self.padding) < profile.DOWNLINK_MTU:
            self.padding += '0'

        self.window_number = int(self.w, 2)

    def to_string(self):
        return self.header + self.padding

    def to_bytes(self):
        return bitstring_to_bytes(self.header + self.padding)

    def length(self):
        return len(self.header + self.padding)

    def is_receiver_abort(self):
        ack_string = self.to_string()
        l2_word_size = self.profile.L2_WORD_SIZE
        header = ack_string[:len(self.rule_id + self.dtag + self.w + self.c)]
        padding = ack_string[len(self.rule_id + self.dtag + self.w + self.c):ack_string.rfind('1') + 1]
        padding_start = padding[:-l2_word_size]
        padding_end = padding[-l2_word_size:]

        if padding_end == "1" * l2_word_size:
            if padding_start != '' and len(header) % l2_word_size != 0:
                return is_monochar(padding_start) and padding_start[0] == '1'
            else:
                return len(header) % l2_word_size == 0
        else:
            return False

    @staticmethod
    def parse_from_hex(profile, h):
        ack = zfill(bin(int(h, 16))[2:], profile.DOWNLINK_MTU)
        ack_index_dtag = profile.RULE_ID_SIZE
        ack_index_w = ack_index_dtag + profile.T
        ack_index_c = ack_index_w + profile.M
        ack_index_bitmap = ack_index_c + 1
        ack_index_padding = ack_index_bitmap + profile.BITMAP_SIZE

        return ACK(profile,
                   ack[:ack_index_dtag],
                   ack[ack_index_dtag:ack_index_w],
                   ack[ack_index_w:ack_index_c],
                   ack[ack_index_c],
                   ack[ack_index_bitmap:ack_index_padding],
                   ack[ack_index_padding:])


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


# Sigfox
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


class Header:
    profile = None

    RULE_ID = ""
    DTAG = ""
    W = ""
    FCN = ""
    C = ""

    string = ""
    bytes = None

    def __init__(self, profile, rule_id, dtag, w, fcn, c=""):  # rule_id is arbitrary, as it's not applicable for F/R

        self.profile = profile

        direction = profile.direction

        if direction == "DOWNLINK":
            self.FCN = ""
            self.C = c

        if len(rule_id) != profile.RULE_ID_SIZE:
            print('RULE must be of length RULE_ID_SIZE')
        else:
            self.RULE_ID = rule_id

        if profile.T == "0":
            self.DTAG = ""
        elif len(dtag) != profile.T:
            print('DTAG must be of length T')
        else:
            self.DTAG = dtag

        if len(w) != profile.M:
            print(w)
            print(profile.M)
            print('W must be of length M')
        else:
            self.W = w

        if fcn != "":
            if len(fcn) != profile.N:
                print('FCN must be of length N')
            else:
                self.FCN = fcn

        self.string = "".join([self.RULE_ID, self.DTAG, self.W, self.FCN, self.C])
        self.bytes = bytes(int(self.string[i:i + 8], 2) for i in range(0, len(self.string), 8))

    def test(self):

        print("HEADER:")
        print(self.string)

        if len(self.string) != self.profile.HEADER_LENGTH:
            print('The header has not been initialized correctly.')

class ReceiverAbort(ACK):

    def __init__(self, profile, header):
        rule_id = header.RULE_ID
        dtag = header.DTAG
        w = header.W

        header = Header(profile=profile,
                        rule_id=rule_id,
                        dtag=dtag,
                        w=w,
                        fcn='',
                        c='1')

        padding = ''
        # if the Header does not end at an L2 Word boundary,
        # append bits set to 1 as needed to reach the next L2 Word boundary.
        while len(header.string + padding) % profile.L2_WORD_SIZE != 0:
            padding += '1'

        # append exactly one more L2 Word with bits all set to ones.
        padding += '1' * profile.L2_WORD_SIZE

        super().__init__(profile, rule_id, dtag, w, c='1', bitmap='', padding=padding)
# Fragment needs for Header and function
class Fragment:
    profile = None
    header_length = 0
    rule_id_size = 0
    t = 0
    n = 0
    window_size = 0

    header = None
    payload = None
    string = ''

    def __init__(self, profile, fragment):
        self.profile = profile

        self.header_length = profile.HEADER_LENGTH
        self.rule_id_size = profile.RULE_ID_SIZE
        self.t = profile.T
        self.n = profile.N
        self.m = profile.M

        header = zfill(str(bin(int.from_bytes(fragment[0], 'big')))[2:], self.header_length)
        payload = fragment[1]

        rule_id = str(header[:self.rule_id_size])
        dtag = str(header[self.rule_id_size:self.rule_id_size + self.t])
        window = str(header[self.rule_id_size + self.t:self.rule_id_size + self.t + self.m])
        fcn = str(header[self.rule_id_size + self.t + self.m:self.rule_id_size + self.t + self.m + self.n])
        c = ""

        self.header = Header(self.profile, rule_id, dtag, window, fcn, c)
        self.payload = payload
        self.bytes = self.header.bytes + self.payload
        self.string = self.bytes.decode()
        self.hex = self.bytes.hex()

    def test(self):
        print(f"Header: {self.header.string}")
        print(f"Payload: {str(self.payload)}")
        print(f"String: {self.string}")
        print(f"Bytes: {self.bytes}")
        print(f"Hex: {self.hex}")

    def is_all_1(self):
        fcn = self.header.FCN
        payload = self.payload.decode()
        return fcn[0] == '1' and is_monochar(fcn) and not (payload[0] == '0' and is_monochar(payload))

    def is_all_0(self):
        fcn = self.header.FCN
        return fcn[0] == '0' and is_monochar(fcn)

    def expects_ack(self):
        return self.is_all_0() or self.is_all_1()

    def is_sender_abort(self):
        fcn = self.header.FCN
        padding = self.payload.decode()
        return fcn[0] == '1' and is_monochar(fcn) and padding[0] == '0' and is_monochar(padding)

# Reassembler needs for fragment
class Reassembler:
    profile = None
    schc_fragments = []
    rule_set = set()
    dtag_set = set()
    window_set = set()
    fcn_set = set()

    def __init__(self, profile, schc_fragments):
        self.profile = profile

        for fragment in schc_fragments:
            if fragment != b'':
                self.schc_fragments.append(Fragment(self.profile, fragment))

        for fragment in self.schc_fragments:
            self.rule_set.add(fragment.header.RULE_ID)
            self.dtag_set.add(fragment.header.DTAG)
            self.window_set.add(fragment.header.W)
            self.fcn_set.add(fragment.header.FCN)

    def reassemble(self):
        fragments = self.schc_fragments
        payload_list = []

        for fragment in fragments:
            payload_list.append(fragment.payload)

        return b"".join(payload_list)

def wyschc_get():
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
    """
    # File where we will store authentication credentials after acquiring them.
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CLIENT_SECRETS_FILE
    # Wait for an HTTP POST request.
    if request.method == 'POST':

        # Get request JSON.
        print("POST RECEIVED")
        request_dict = request.get_json()
        print('Received Sigfox message: {}'.format(request_dict))

        # Get data and Sigfox Sequence Number.
        raw_data = request_dict["data"]
        sigfox_sequence_number = request_dict["seqNumber"]
        ack_req = request_dict["ack"]

        # Initialize Cloud Storage variables.
        # BUCKET_NAME = config.BUCKET_NAME

        header_first_hex = raw_data[:1]
        if header_first_hex == '0' or header_first_hex == '1':
            header = bytes.fromhex(raw_data[:2])
            payload = bytearray.fromhex(raw_data[2:])
            header_bytes = 1
        elif header_first_hex == '2':
            header = bytearray.fromhex(raw_data[:4])
            payload = bytearray.fromhex(raw_data[4:])
            header_bytes = 2
        else:
            print("Wrong header in raw_data")
            return 'wrong header', 204

        # Initialize SCHC variables.
        profile = Sigfox("UPLINK", "ACK ON ERROR", header_bytes)
        n = profile.N
        m = profile.M

        # If fragment size is greater than buffer size, ignore it and end function.
        if len(raw_data) / 2 * 8 > profile.UPLINK_MTU:  # Fragment is hex, 1 hex = 1/2 byte
            return json.dumps({"message": "Fragment size is greater than buffer size"}), 200

        # If the folder named "all windows" does not exist, create it along with all subdirectories.
        initialize_blobs(BUCKET_NAME, profile)

        # Compute the fragment compressed number (FCN) from the Profile
        fcn_dict = {}
        for j in range(2 ** n - 1):
            fcn_dict[zfill(bin((2 ** n - 2) - (j % (2 ** n - 1)))[2:], 3)] = j

        # Parse raw_data into "data = [header, payload]
        # Convert to a Fragment class for easier manipulation.
        header = bytes.fromhex(raw_data[:2])
        payload = bytearray.fromhex(raw_data[2:])
        data = [header, payload]
        fragment_message = Fragment(profile, data)

        if fragment_message.is_sender_abort():
            try:
                _ = requests.post(url='http://localhost:5000/cleanup',
                                  json={"header_bytes": header_bytes},
                                  timeout=0.1)
            except requests.exceptions.ReadTimeout:
                pass
            return 'Sender-Abort received', 204

        # Get data from this fragment.
        fcn = fragment_message.header.FCN
        rule_id = fragment_message.header.RULE_ID
        dtag = fragment_message.header.DTAG
        current_window = int(fragment_message.header.W, 2)

        # Get the current bitmap.
        bitmap = read_blob(BUCKET_NAME, f"all_windows/window_{current_window}/bitmap_{current_window}")

        # Controlling deterministic losses. This loads the file "loss_mask.txt" which states when should a fragment be
        # lost, separated by windows.
        fd = None
        try:
            fd = open(LOSS_MASK_MODIFIED, "r")
        except FileNotFoundError:
            fd = open(LOSS_MASK, "r")
        finally:
            loss_mask = []
            for line in fd:
                if not line.startswith("#"):
                    for char in line:
                        try:
                            loss_mask.append(int(char))
                        except ValueError:
                            pass
            fd.close()

        print(f"Loss mask: {loss_mask}")

        # Controlling random losses.
        if 'enable_losses' in request_dict and not (fragment_message.is_all_0() or fragment_message.is_all_1()):
            if request_dict['enable_losses']:
                loss_rate = request_dict["loss_rate"]
                # loss_rate = 10
                coin = random.random()
                print(f'loss rate: {loss_rate}, random toss:{coin * 100}')
                if coin * 100 < loss_rate:
                    print("[LOSS] The fragment was lost.")
                    return 'fragment lost', 204

        # Check if the fragment is an All-1
        if is_monochar(fcn) and fcn[0] == '1':
            print("[RECV] This is an All-1.")

            # Check if fragment is to be lost (All-1 is the very last fragment)
            if loss_mask[-1] != 0:
                loss_mask[-1] -= 1
                with open("loss_mask_modified.txt", "w") as fd:
                    for i in loss_mask:
                        fd.write(str(i))
                print(f"[RECV] Fragment lost.")
                return 'fragment lost', 204

            # Inactivity timer validation
            time_received = int(request_dict["time"])

            if exists_blob(BUCKET_NAME, "timestamp"):
                # Check time validation.
                last_time_received = int(read_blob(BUCKET_NAME, "timestamp"))
                print(f"[RECV] Previous timestamp: {last_time_received}")
                print(f"[RECV] This timestamp: {time_received}")

                # If the inactivity timer has been reached, abort communication.
                if time_received - last_time_received > profile.INACTIVITY_TIMER_VALUE:
                    print("[RECV] Inactivity timer reached. Ending session.")
                    receiver_abort = ReceiverAbort(profile, fragment_message.header)
                    print("Sending Receiver Abort")
                    response_json = send_ack(request_dict, receiver_abort)
                    print(f"Response content -> {response_json}")
                    try:
                        _ = requests.post(url='http://localhost:5000/cleanup',
                                          json={"header_bytes": header_bytes},
                                          timeout=0.1)
                    except requests.exceptions.ReadTimeout:
                        pass
                    return response_json, 200

            # Update timestamp
            upload_blob(BUCKET_NAME, time_received, "timestamp")

            # Update bitmap and upload it.
            bitmap = replace_bit(bitmap, len(bitmap) - 1, '1')
            print(f"Bitmap is now {bitmap}")
            upload_blob(BUCKET_NAME,
                        bitmap,
                        f"all_windows/window_{current_window}/bitmap_{current_window}")
            # Upload the fragment data.
            upload_blob(BUCKET_NAME,
                        data[0].decode("utf-8") + data[1].decode("utf-8"),
                        f"all_windows/window_{current_window}/fragment_{current_window}_{profile.WINDOW_SIZE - 1}")

        # Else, it is a normal fragment.
        else:
            fragment_number = fcn_dict[fragment_message.header.FCN]

            # Check if fragment is to be lost
            position = current_window * profile.WINDOW_SIZE + fragment_number
            if loss_mask[position] != 0:
                loss_mask[position] -= 1
                with open(LOSS_MASK_MODIFIED, "w") as fd:
                    for i in loss_mask:
                        fd.write(str(i))
                print(f"[RECV] Fragment lost.")
                return 'fragment lost', 204

            # Inactivity timer validation
            time_received = int(request_dict["time"])

            if exists_blob(BUCKET_NAME, "timestamp"):
                # Check time validation.
                last_time_received = int(read_blob(BUCKET_NAME, "timestamp"))
                print(f"[RECV] Previous timestamp: {last_time_received}")
                print(f"[RECV] This timestamp: {time_received}")

                # If the inactivity timer has been reached, abort communication.
                if time_received - last_time_received > profile.INACTIVITY_TIMER_VALUE:
                    print("[RECV] Inactivity timer reached. Ending session.")
                    receiver_abort = ReceiverAbort(profile, fragment_message.header)
                    print("Sending Receiver Abort")
                    response_json = send_ack(request_dict, receiver_abort)
                    print(f"Response content -> {response_json}")
                    try:
                        _ = requests.post(url='http://localhost:5000/cleanup',
                                          json={"header_bytes": header_bytes},
                                          timeout=0.1)
                    except requests.exceptions.ReadTimeout:
                        pass
                    return response_json, 200

            # Update timestamp
            upload_blob(BUCKET_NAME, time_received, "timestamp")

            # Update Sigfox sequence number JSON
            sequence_numbers = json.loads(read_blob(BUCKET_NAME, "SSN"))
            sequence_numbers[position] = request_dict["seqNumber"]
            print(sequence_numbers)
            upload_blob(BUCKET_NAME, json.dumps(sequence_numbers), "SSN")

            upload_blob(BUCKET_NAME, fragment_number, "fragment_number")

            # Print some data for the user.
            print(f"[RECV] This corresponds to the {str(fragment_number)}th fragment "
                  f"of the {str(current_window)}th window.")
            print(f"[RECV] Sigfox sequence number: {str(sigfox_sequence_number)}")

            # Update bitmap and upload it.
            bitmap = replace_bit(bitmap, fragment_number, '1')
            print(f"Bitmap is now {bitmap}")
            upload_blob(BUCKET_NAME, bitmap, f"all_windows/window_{current_window}/bitmap_{current_window}")

            # Upload the fragment data.
            upload_blob(BUCKET_NAME,
                        data[0].decode("utf-8") + data[1].decode("utf-8"),
                        f"all_windows/window_{current_window}/fragment_{current_window}_{fragment_number}")

        # If the fragment requests an ACK...
        if ack_req:

            # Prepare the ACK bitmap. Find the first bitmap with a 0 in it.
            # This bitmap corresponds to the lowest-numered window with losses.
            bitmap_ack = None
            window_ack = None
            for i in range(current_window + 1):
                bitmap_ack = read_blob(BUCKET_NAME, f"all_windows/window_{i}/bitmap_{i}")
                print(bitmap_ack)
                window_ack = i
                if '0' in bitmap_ack:
                    break

            # The final window is only accessible through All-1.
            # If All-0, check non-final windows
            if fragment_message.is_all_0():
                # If the ACK bitmap has a 0 at a non-final window, a fragment has been lost.
                if '0' in bitmap_ack:
                    print("[ALL0] Lost fragments have been detected. Preparing ACK.")
                    print(f"[ALL0] Bitmap with errors -> {bitmap_ack}")
                    ack = ACK(profile=profile,
                              rule_id=rule_id,
                              dtag=dtag,
                              w=zfill(format(window_ack, 'b'), m),
                              c='0',
                              bitmap=bitmap_ack)
                    response_json = send_ack(request_dict, ack)
                    print(f"Response content -> {response_json}")
                    print("[ALL0] ACK sent.")
                    return response_json, 200
                # If all bitmaps are complete up to this point, no losses are detected.
                else:
                    print("[ALL0] No losses have been detected.")
                    print("Response content -> ''")
                    return '', 204

            # If the fragment is All-1, the last window should be considered.
            if fragment_message.is_all_1():

                # First check for 0s in the bitmap. If the bitmap is of a non-final window, send corresponding ACK.
                if current_window != window_ack and '0' in bitmap_ack:
                    print("[ALL1] Lost fragments have been detected. Preparing ACK.")
                    print(f"[ALL1] Bitmap with errors -> {bitmap_ack}")
                    ack = ACK(profile=profile,
                              rule_id=rule_id,
                              dtag=dtag,
                              w=zfill(format(window_ack, 'b'), m),
                              c='0',
                              bitmap=bitmap_ack)
                    response_json = send_ack(request_dict, ack)
                    print(f"Response content -> {response_json}")
                    print("[ALL1] ACK sent.")
                    return response_json, 200

                # If the bitmap is of the final window, check the following regex.
                else:
                    # The bitmap in the last window follows the following regular expression: "1*0*1*"
                    # Since the ALL-1, if received, changes the least significant bit of the bitmap.
                    # For a "complete" bitmap in the last window, there shouldn't be non-consecutive zeroes:
                    # 1110001 is a valid bitmap, 1101001 is not.
                    # The bitmap may or may not contain the 0s.
                    pattern = re.compile("1*0*1")

                    # If the bitmap matches the regex, check if there are still lost fragments.
                    if pattern.fullmatch(bitmap_ack) is not None:
                        # The idea is the following:
                        # Assume a fragment has been lost, but the regex has been matched.
                        # For example, we want a bitmap 1111111 but due to a loss we have 1111101.
                        # This incomplete bitmap matches the regex.
                        # We should note that here the SSN of the All-1 and the penultimate fragment received
                        # are not consecutive.
                        # Retransmitting the lost fragment and resending the All-1 solves that problem.
                        # There is another problematic case: we want a bitmap 1111111 but due to losses we have 1111001.
                        # If the second of those two lost fragments is retransmitted, the new bitmap, 1111011, does not
                        # match the regex. If, instead, the first of those fragments is retransmitted, the new bitmap
                        # 1111101 does match the regex. As the sender should retransmit these messages sequentially,
                        # the SSN of the resent All-1 and the penultimate fragment are still not consecutive.
                        # The only way for these two SSNs to be consecutive in these cases
                        # is that the penultimate fragment fills the bitmap in the 6th bit,
                        # and the last fragment is the All-1.
                        # This reasoning is still valid when the last window does not contain WINDOW_SIZE fragments.
                        # These particular cases validate the use for this regex matching.
                        # Remember that 1111011 is NOT a valid bitmap.
                        # In conclusion, AFTER the regex matching,
                        # we should check if the SSNs of the two last received fragments are consecutive.
                        # The second to last fragment has the highest SSN registered in the JSON.
                        # TODO: What happens when the All-0 prior to the last window is lost and is retransmitted with the All-1?
                        # We should consider only the SSNs of the last window. If there is a retransmission in a window
                        # prior to the last, the reasoning fails since the All-1 is always consecutive to a
                        # retransmitted fragment of a non-final window.
                        # If the All-1 is the only fragment of the last window (bitmap 0000001), and bitmap check of
                        # prior windows has passed, check the consecutiveness of the last All-0 and the All-1.

                        sequence_numbers = json.loads(read_blob(BUCKET_NAME, "SSN"))

                        # This array has the SSNs of the last window.
                        # last_window_ssn = list(sequence_numbers.values())[current_window * profile.WINDOW_SIZE + 1:]

                        # If this array is empty, no messages have been received in the last window. Check if the
                        # last All-0 and the All-1 are consecutive. If they are not, there are lost fragments. If they
                        # are, the All-0 may have been retransmitted.
                        # print(last_window_ssn)

                        # The last sequence number should be the highest of these values.
                        last_sequence_number = max(list(map(int, list(sequence_numbers.values()))))

                        # TODO: If the All-0 has the highest of these values, it may have been retransmitted using the All-1

                        print(f"All-1 sequence number {sigfox_sequence_number}")
                        print(f"Last sequence number {last_sequence_number}")

                        if int(sigfox_sequence_number) - int(last_sequence_number) == 1:
                            print("[ALL1] Integrity checking complete, launching reassembler.")
                            # All-1 does not define a fragment number, so its fragment number must be the next
                            # of the higest registered fragment number.
                            last_index = max(list(map(int, list(sequence_numbers.keys())))) + 1
                            upload_blob_using_threads(BUCKET_NAME,
                                                      data[0].decode("ISO-8859-1") + data[1].decode("utf-8"),
                                                      f"all_windows/window_{current_window}/"
                                                      f"fragment_{current_window}_{last_index}")
                            try:
                                _ = requests.post(url='http://localhost:5000/http_reassemble',
                                                  json={"last_index": last_index,
                                                        "current_window": current_window,
                                                        "header_bytes": header_bytes}, timeout=0.1)
                            except requests.exceptions.ReadTimeout:
                                pass

                            # Send last ACK to end communication (on receiving an All-1, if no fragments are lost,
                            # if it has received at least one tile, return an ACK for the highest numbered window we
                            # currently have tiles for).
                            print("[ALL1] Preparing last ACK")
                            bitmap = ''
                            for k in range(profile.BITMAP_SIZE):
                                bitmap += '0'
                            last_ack = ACK(profile=profile,
                                           rule_id=rule_id,
                                           dtag=dtag,
                                           w=zfill(format(window_ack, 'b'), m),
                                           c='1',
                                           bitmap=bitmap_ack)
                            response_json = send_ack(request_dict, last_ack)
                            print(f"200, Response content -> {response_json}")
                            print("[ALL1] Last ACK has been sent.")

                            return response_json, 200
                    # If the last two fragments are not consecutive, or the bitmap didn't match the regex,
                    # send an ACK reporting losses.
                    else:
                        # Send NACK at the end of the window.
                        print("[ALLX] Sending NACK for lost fragments...")
                        ack = ACK(profile=profile,
                                  rule_id=rule_id,
                                  dtag=dtag,
                                  w=zfill(format(window_ack, 'b'), m),
                                  c='0',
                                  bitmap=bitmap_ack)
                        response_json = send_ack(request_dict, ack)
                        return response_json, 200

        return '', 204

    else:
        print('Invalid HTTP Method to invoke Cloud Function. Only POST supported')
        return abort(405)
