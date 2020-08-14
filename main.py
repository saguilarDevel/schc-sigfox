import os
import json
from flask import abort
from google.cloud import storage
from math import ceil, floor

from Entities.Fragmenter import Fragmenter
from Entities.Sigfox import Sigfox
from Messages.Fragment import Fragment

from Entities.Reassembler import Reassembler
from Messages.ACK import ACK
from Messages.Fragment import Fragment

def upload_blob(bucket_name, blob_text, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(blob_text)
    print('File uploaded to {}.'.format(destination_blob_name))

def read_blob(bucket_name, blob_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    return blob.download_as_string()
def delete_blob(bucket_name, blob_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    blob.delete()
def exists_blob(bucket_name, blob_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.exists()
def create_folder(bucket_name, folder_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(folder_name)
    blob.upload_from_string("")
    print('Folder uploaded to {}.'.format(folder_name))
def size_blob(bucket_name, blob_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.size
def send_ack(request, ack):
    device = request["device"]
    response_dict = {device: {'downlinkData': ack.to_bytes()}}
    response_json = json.dumps(response_dict)
    return response_json

def hello_get(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
    """
    if request.method == 'POST':
        print("POST RECEIVED")
        BUCKET_NAME = 'sigfoxschc'
        request_dict = request.get_json()
        print('Received Sigfox message: {}'.format(request_dict))

        # print("Loading classes...")
        fragment = request_dict["data"]
        sigfox_sequence_number = request_dict["seqNumber"]
        if exists_blob(BUCKET_NAME, "SSN"):
            last_sequence_number = read_blob(BUCKET_NAME, "SSN")

        # CHECK TIME VALIDATION (INACTIVITY TIMER)
        time_received = request_dict["time"]
        BLOB_NAME = "timestamp"
        BLOB_STR = time_received
        upload_blob(BUCKET_NAME, BLOB_STR, BLOB_NAME)
        print("Hasta aqui llegamos.")

        profile_uplink = Sigfox("UPLINK", "ACK ON ERROR")
        profile_downlink = Sigfox("DOWNLINK", "NO ACK")
        buffer_size = profile_uplink.MTU
        n = profile_uplink.N
        m = profile_uplink.M

        if len(fragment) * 8 > buffer_size:
            print("Fragment size is greater than buffer size D:")
            exit(0)

        print("Loading functions...")

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

        fragment = request_dict["data"]
        sigfox_sequence_number = request_dict["seqNumber"]
        if exists_blob(BUCKET_NAME, "SSN"):
            last_sequence_number = read_blob(BUCKET_NAME, "SSN")

        # CHECK TIME VALIDATION (INACTIVITY TIMER)
        time_received = request_dict["time"]
        BLOB_NAME = "timestamp"
        BLOB_STR = time_received
        upload_blob(BUCKET_NAME, BLOB_STR, BLOB_NAME)

        profile_uplink = Sigfox("UPLINK", "ACK ON ERROR")
        profile_downlink = Sigfox("DOWNLINK", "NO ACK")
        buffer_size = profile_uplink.MTU
        n = profile_uplink.N
        m = profile_uplink.M

        if len(fragment) * 8 > buffer_size:
            print("Fragment size is greater than buffer size D:")
            # exit(0)
            return json.dumps({"message": "Fragment size is greater than buffer size D:"}), 200



        if not exists_blob(BUCKET_NAME, "all_windows/"):
            create_folder(BUCKET_NAME, "all_windows/")
            for i in range(2 ** m):
                create_folder(BUCKET_NAME, "all_windows/window_%d/" % i)
                for j in range(2 ** n - 1):
                    upload_blob(BUCKET_NAME, "", "all_windows/window_%d/fragment_%d_%d" % (i, i, j))
                # create bitmap for each window
                if not exists_blob(BUCKET_NAME, "all_windows/window_%d/bitmap_%d" % (i, i) or size_blob(
                        "all_windows/window_%d/bitmap_%d" % (i, i)) == 0):
                    bitmap = ""
                    for b in range(profile_uplink.BITMAP_SIZE):
                        bitmap += "0"
                    upload_blob(BUCKET_NAME, bitmap, "all_windows/window_%d/bitmap_%d" % (i, i))

        print("BLOB Created")
        window = []
        for i in range(2 ** n - 1):
            window.append([b"", b""])

        fcn_dict = {}
        for j in range(2 ** n - 1):
            fcn_dict[zfill(bin((2 ** n - 2) - (j % (2 ** n - 1)))[2:], 3)] = j

        # A fragment has the format "fragment = [header, payload]".
        data = [bytes([fragment[0]]), bytearray(fragment[1:])]
        print("data {}".format(data))
        # Convert to a Fragment class for easier manipulation.
        fragment_message = Fragment(profile_uplink, data)
        current_window = int(fragment_message.header.W, 2)

        bitmap = read_blob(BLOB_NAME, "all_windows/window_%d/bitmap_%d" % (current_window, current_window))

        # try:
        #     fragment_number = fcn_dict[fragment_message.header.FCN]
        #
        #     print("[RECV] This corresponds to the " + str(fragment_number) + "th fragment of the " + str(
        #         current_window) + "th window.")
        #     print("[RECV] Sigfox sequence number: " + str(sigfox_sequence_number))
        #
        #     bitmap = replace_bit(bitmap, fragment_number, '1')
        #
        #     upload_blob(BUCKET_NAME, bitmap, "all_windows/window_%d/bitmap_%d" % (current_window, current_window))
        #     upload_blob(BUCKET_NAME, data[0].decode("utf-8") + data[1].decode("utf-8"),
        #                 "all_windows/window_%d/fragment_%d_%d" % (current_window, current_window, fragment_number))
        #
        # except KeyError:
        #
        #     print("[RECV] This seems to be the final fragment.")
        #
        #     bitmap = replace_bit(bitmap, len(bitmap) - 1, '1')
        #     upload_blob(BUCKET_NAME, bitmap, "all_windows/window_%d/bitmap_%d" % (current_window, current_window))
        #
        # rule_id = fragment_message.header.RULE_ID
        # dtag = fragment_message.header.DTAG
        # w = fragment_message.header.W
        # upload_blob(BUCKET_NAME, sigfox_sequence_number, "SSN")
        #
        # if fragment_message.is_all_0() or fragment_message.is_all_1():
        #     for i in range(current_window + 1):
        #         bitmap_ack = read_blob(BUCKET_NAME, "all_windows/window_%d/bitmap%d" % (i, i))
        #         window_ack = i
        #         if '0' in bitmap_ack:
        #             break
        #
        #     if '0' in bitmap_ack and fragment_message.is_all_0():
        #         print("[ALLX] Sending ACK for lost fragments...")
        #         ack = ACK(profile_downlink, rule_id, dtag, zfill(format(window_ack, 'b'), m), bitmap_ack, '0')
        #         response_json = send_ack(request_dict, ack)
        #         return response_json, 200
        #
        #     if fragment_message.is_all_0() and bitmap[0] == '1' and all(bitmap):
        #         print("[ALLX] Sending ACK after window...")
        #         ack = ACK(profile_downlink, rule_id, dtag, w, bitmap, '0')
        #         response_json = send_ack(request_dict, ack)
        #         return response_json, 200
        #
        #     if fragment_message.is_all_1():
        #         last_index = 0
        #         last_received_index = 0
        #         i = 0
        #         j = 0
        #
        #         while i < 2 ** n - 1:
        #             if size_blob(BUCKET_NAME,
        #                          "all_windows/window%d/fragment%d_%d" % (current_window, current_window, i)) == 0:
        #                 last_index = i
        #                 break
        #             else:
        #                 i += 1
        #
        #         while j < 2 ** n - 1:
        #             if exists_blob(BUCKET_NAME, "all_windows/window_%d/fragment%d_%d" % (
        #             current_window, current_window, j)) and size_blob(BUCKET_NAME, "all_windows/window_%d/fragment%d_%d" % (
        #             current_window, current_window, j)) != 0:
        #                 last_received_index = j + 1
        #             j += 1
        #
        #         if last_index != last_received_index:
        #             print("[ALLX] Sending NACK for lost fragments...")
        #             ack = ACK(profile_downlink, rule_id, dtag, zfill(format(window_ack, 'b'), m), bitmap_ack, '0')
        #             response_json = send_ack(request_dict, ack)
        #             return response_json, 200
        #
        #         else:
        #             fragments = []
        #             upload_blob(BUCKET_NAME, data[0].decode("utf-8") + data[1].decode("utf-8"),
        #                         "all_windows/window_%d/fragment_%d_%d" % (current_window, current_window, last_index))
        #
        #             for i in range(2 ** m):
        #                 for j in range(2 ** n - 1):
        #                     fragment_file = open("./all_windows/window_%d/fragment_%d_%d" % (i, i, j), "r")
        #                     ultimate_header = fragment_file.read(1)
        #                     ultimate_payload = fragment_file.read()
        #                     ultimate_fragment = [ultimate_header.encode(), ultimate_payload.encode()]
        #                     fragments.append(ultimate_fragment)
        #
        #             print("[ALL1] Last fragment. Reassembling...")
        #             reassembler = Reassembler(profile_uplink, fragments)
        #             payload = bytearray(reassembler.reassemble())
        #             upload_blob(BLOB_NAME, payload.decode("utf-8"), "PAYLOAD")
        #
        #             print("[ALL1] Reassembled: Sending last ACK")
        #             bitmap = ''
        #             for k in range(profile_uplink.BITMAP_SIZE):
        #                 bitmap += '0'
        #             last_ack = ACK(profile_downlink, rule_id, dtag, w, bitmap, '1')
        #             response_json = send_ack(request_dict, last_ack)
        #             return response_json, 200

    #     return '', 204
    #
    # else:
    #     print('Invalid HTTP Basic Authentication: {}'.format(request.authorization))
    #     return abort(401)
    else:
        print('Invalid HTTP Method to invoke Cloud Function. Only POST supported')
        return abort(405)

    # else:
    #     print("GET RECEIVED")

    return 'Hello World!'

