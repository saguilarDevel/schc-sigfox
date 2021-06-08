import filecmp
import os
import random
import re

import requests
from flask import Flask, request
from flask import abort

import config.config as config
from Entities.Reassembler import Reassembler
from Entities.Sigfox import Sigfox
from Messages.ACK import ACK
from Messages.Fragment import Fragment
from Messages.ReceiverAbort import ReceiverAbort
from firebase_utils import *
from schc_utils import *

app = Flask(__name__)


@app.route('/schc_receiver', methods=['GET', 'POST'])
def schc_receiver():
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
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.CLIENT_SECRETS_FILE
    # Wait for an HTTP POST request.
    if request.method == 'POST':

        # Get request JSON.
        print("POST RECEIVED")
        request_dict = request.get_json()
        print('Received Sigfox message: {}'.format(request_dict))

        # Get data and Sigfox Sequence Number.
        fragment = request_dict["data"]
        sigfox_sequence_number = request_dict["seqNumber"]
        ack_req = request_dict["ack"]

        # Initialize Cloud Storage variables.
        BUCKET_NAME = config.BUCKET_NAME

        header_first_hex = fragment[0]

        if header_first_hex == '0' or header_first_hex == '1':
            header = bytes.fromhex(fragment[:2])
            payload = bytearray.fromhex(fragment[2:])
            header_bytes = 1
        elif header_first_hex == 'f' or header_first_hex == '2':
            header = bytearray.fromhex(fragment[:4])
            payload = bytearray.fromhex(fragment[4:])
            header_bytes = 2
        else:
            print("Wrong header in fragment")
            return 'wrong header', 204

        data = [header, payload]

        # Initialize SCHC variables.
        profile = Sigfox("UPLINK", "ACK ON ERROR", header_bytes)
        buffer_size = profile.UPLINK_MTU
        n = profile.N
        m = profile.M

        # If fragment size is greater than buffer size, ignore it and end function.
        if len(fragment) / 2 * 8 > buffer_size:  # Fragment is hex, 1 hex = 1/2 byte
            return json.dumps({"message": "Fragment size is greater than buffer size D:"}), 200

        # Initialize empty window
        window = []
        for i in range(2 ** n - 1):
            window.append([b"", b""])

        # Compute the fragment compressed number (FCN) from the Profile
        fcn_dict = {}
        for j in range(2 ** n - 1):
            fcn_dict[zfill(bin((2 ** n - 2) - (j % (2 ** n - 1)))[2:], n)] = j

        # Convert to a Fragment class for easier manipulation.
        fragment_message = Fragment(profile, data)

        # Get current window for this fragment.
        current_window = int(fragment_message.HEADER.W, 2)

        # Get the current bitmap.
        bitmap = read_blob("all_windows/window_%d/bitmap_%d" % (current_window, current_window))


        if fragment_message.is_sender_abort():
            print("Sender-Abort received")
            return 'Sender-Abort received', 204

        try:
            fragment_number = fcn_dict[fragment_message.HEADER.FCN]
            upload_blob(fragment_number, "fragment_number")

            time_received = int(request_dict["time"])
            if exists_blob("timestamp"):
                # Check time validation.
                last_time_received = int(read_blob("timestamp"))

                # If this is not the very first fragment and the inactivity timer has been reached, ignore the message.
                if str(fragment_number) != "0" and str(
                        current_window) != "0" and time_received - last_time_received > profile.INACTIVITY_TIMER_VALUE:
                    print("[RECV] Inactivity timer reached. Ending session.")
                    receiver_abort = ReceiverAbort(profile, fragment_message.HEADER)
                    print("Sending Receiver Abort")
                    response_json = send_ack(request_dict, receiver_abort)
                    print(f"Response content -> {response_json}")
                    return response_json, 200

            # Upload current timestamp.
            upload_blob(time_received, "timestamp")

            # Print some data for the user.
            print("[RECV] This corresponds to the " + str(fragment_number) + "th fragment of the " + str(
                current_window) + "th window.")
            print("[RECV] Sigfox sequence number: " + str(sigfox_sequence_number))

            # Update bitmap and upload it.
            bitmap = replace_bit(bitmap, fragment_number, '1')
            upload_blob(bitmap, "all_windows/window_%d/bitmap_%d" % (current_window, current_window))

            # Upload the fragment data.
            upload_blob(data[0].decode("ISO-8859-1") + data[1].decode("utf-8"),
                        "all_windows/window_%d/fragment_%d_%d" % (current_window, current_window, fragment_number))

        # If the FCN could not been found, it almost certainly is the final fragment.
        except KeyError:
            print("[RECV] This seems to be the final fragment.")
            # Upload current timestamp.
            time_received = int(request_dict["time"])
            upload_blob(time_received, "timestamp")
            print("is All-1:{}, is All-0:{}".format(fragment_message.is_all_1(), fragment_message.is_all_0()))
            # print("RULE_ID: {}, W:{}, FCN:{}".format(fragment.header.RULE_ID, fragment.header.W, fragment.header.FCN))
            # Update bitmap and upload it.
            bitmap = replace_bit(bitmap, len(bitmap) - 1, '1')
            upload_blob(bitmap, "all_windows/window_%d/bitmap_%d" % (current_window, current_window))

        # Get some SCHC values from the fragment.
        rule_id = fragment_message.HEADER.RULE_ID
        dtag = fragment_message.HEADER.DTAG
        w = fragment_message.HEADER.W

        # Get last and current Sigfox sequence number (SSN)
        last_sequence_number = 0
        if exists_blob("SSN"):
            last_sequence_number = read_blob("SSN")
        upload_blob(sigfox_sequence_number, "SSN")

        # # Controlling deterministic losses. This loads the file "loss_mask.txt" which states when should a fragment be
        # # lost, separated by windows.
        # fd = None
        # try:
        #     fd = open(config.LOSS_MASK_MODIFIED, "r")
        # except FileNotFoundError:
        #     fd = open(config.LOSS_MASK, "r")
        # finally:
        #     loss_mask = []
        #     for line in fd:
        #         if not line.startswith("#"):
        #             for char in line:
        #                 try:
        #                     loss_mask.append(int(char))
        #                 except ValueError:
        #                     pass
        #     fd.close()
        #
        # print(f"Loss mask: {loss_mask}")

        # If the fragment is at the end of a window (ALL-0 or ALL-1)
        if fragment_message.is_all_0() or fragment_message.is_all_1():

            # Prepare the ACK bitmap. Find the first bitmap with a 0 in it.
            for i in range(current_window + 1):
                bitmap_ack = read_blob("all_windows/window_%d/bitmap_%d" % (i, i))
                print(bitmap_ack)
                window_ack = i
                if '0' in bitmap_ack:
                    break

            # If the ACK bitmap has a 0 at the end of a non-final window, a fragment has been lost.
            if fragment_message.is_all_0() and '0' in bitmap_ack:
                print("[ALL0] Sending ACK for lost fragments...")
                print("bitmap with errors -> {}".format(bitmap_ack))
                # Create an ACK message and send it.
                ack = ACK(profile=profile,
                          rule_id=rule_id,
                          dtag=dtag,
                          w=zfill(format(window_ack, 'b'), m),
                          c='0',
                          bitmap=bitmap_ack)
                response_json = send_ack(request_dict, ack)
                print("Response content -> {}".format(response_json))
                return response_json, 200

            # If the ACK bitmap is complete and the fragment is an ALL-0, don't send an ACK
            if fragment_message.is_all_0() and bitmap[0] == '1' and all(bitmap):
                print("[ALL0] All Fragments of current window received")
                print("[ALL0] No need to send an ACK")
                # print("[ALLX] Sending ACK after window...")
                # Create an ACK message and send it.
                # ack = ACK(profile_downlink, rule_id, dtag, w, bitmap, '0')
                # response_json = send_ack(request_dict, ack)
                # print("200, Response content -> {}".format(response_json))
                # Response to continue, no ACK is sent Back.
                return '', 204
                # return response_json, 200

            # If the fragment is an ALL-1
            if fragment_message.is_all_1():

                # The bitmap in the last window follows the following regular expression: "1*0*1*"
                # Since the ALL-1, if received, changes the least significant bit of the bitmap.
                # For a "complete" bitmap in the last window, there shouldn't be non-consecutive zeroes:
                # 1110001 is a valid bitmap, 1101001 is not.

                pattern = re.compile("1*0*1")
                # If the bitmap matches the regex, check if the last two received fragments are consecutive.
                if pattern.fullmatch(bitmap_ack):
                    print("SSN is {} and last SSN is {}".format(sigfox_sequence_number, last_sequence_number))
                    # If the last two received fragments are consecutive, accept the ALL-1 and start reassembling
                    if int(sigfox_sequence_number) - int(last_sequence_number) == 1:
                        last_index = int(read_blob("fragment_number")) + 1
                        upload_blob(data[0].decode("ISO-8859-1") + data[1].decode("utf-8"),
                                    "all_windows/window_%d/fragment_%d_%d" % (
                                        current_window, current_window, last_index))
                        print("Info for reassemble: last_index:{}, current_window:{}".format(last_index,
                                                                                             current_window))
                        try:
                            print('Activating reassembly process...')
                            _ = requests.post(url=config.REASSEMBLE_URL,
                                              json={"last_index": last_index, "current_window": current_window,
                                                    "header_bytes": header_bytes},
                                              timeout=0.1)
                        except requests.exceptions.ReadTimeout:
                            pass
                        # Send last ACK to end communication.
                        print("[ALL1] Reassembled: Sending last ACK")
                        bitmap = ''
                        for k in range(profile.BITMAP_SIZE):
                            bitmap += '0'
                        last_ack = ACK(profile=profile,
                                       rule_id=rule_id,
                                       dtag=dtag,
                                       w=zfill(format(window_ack, 'b'), m),
                                       c='1',
                                       bitmap=bitmap)
                        response_json = send_ack(request_dict, last_ack)
                        # return response_json, 200
                        # response_json = send_ack(request_dict, last_ack)
                        print("200, Response content -> {}".format(response_json))
                        return response_json, 200
                    else:
                        # Send NACK at the end of the window.
                        print("[ALLX] Sending NACK for lost fragments because of SSN...")
                        ack = ACK(profile=profile,
                                  rule_id=rule_id,
                                  dtag=dtag,
                                  w=zfill(format(window_ack, 'b'), m),
                                  c='0',
                                  bitmap=bitmap_ack)
                        response_json = send_ack(request_dict, ack)
                        return response_json, 200
                    # If they are not, there is a gap between two fragments: a fragment has been lost.
                # The same happens if the bitmap doesn't match the regex.
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


@app.route('/reassemble', methods=['GET', 'POST'])
def reassemble():

    if request.method == "POST":
        # Get request JSON.
        print("[REASSEMBLE] POST RECEIVED")
        request_dict = request.get_json()
        print('Received HTTP message: {}'.format(request_dict))

        current_window = int(request_dict["current_window"])
        last_index = int(request_dict["last_index"])
        header_bytes = int(request_dict["header_bytes"])

        # Initialize Cloud Storage variables.
        BUCKET_NAME = config.BUCKET_NAME

        # Initialize SCHC variables.
        profile = Sigfox("UPLINK", "ACK ON ERROR", header_bytes)

        print("[RSMB] Loading fragments")

        # Get all the fragments into an array in the format "fragment = [header, payload]"
        fragments = []

        # For each window, load every fragment into the fragments array
        for i in range(current_window + 1):
            for j in range(profile.WINDOW_SIZE):
                print("Loading fragment {}".format(j))
                fragment_file = read_blob("all_windows/window_%d/fragment_%d_%d" % (i, i, j))
                print(fragment_file)
                header = fragment_file[:header_bytes]
                payload = fragment_file[header_bytes:]
                fragment = [header.encode(), payload.encode()]
                fragments.append(fragment)
                if i == current_window and j == last_index:
                    break

        # Instantiate a Reassembler and start reassembling.
        reassembler = Reassembler(profile, fragments)
        payload = bytearray(reassembler.reassemble())
        # Upload the full message.
        upload_blob(payload.decode("utf-8"), "Reassembled_Packet")

        if filecmp.cmp(config.PAYLOAD, config.MESSAGE):
            print("The reassembled file is equal to the original message.")
        else:
            print("The reassembled file is corrupt.")

        try:
            _ = requests.post(url=config.CLEAN_URL,
                              json={"header_bytes": header_bytes},
                              timeout=0.1)
        except requests.exceptions.ReadTimeout:
            pass

        return '', 204


@app.route('/clean', methods=['GET', 'POST'])
def clean():
    # Wait for an HTTP POST request.
    if request.method == 'POST':

        # Get request JSON.
        print("POST RECEIVED")
        request_dict = request.get_json()
        print('Received Sigfox message: {}'.format(request_dict))

        # Get data and Sigfox Sequence Number.
        header_bytes = int(request_dict["header_bytes"])
        profile = Sigfox("UPLINK", "ACK ON ERROR", header_bytes)
        bitmap = '0' * (2 ** profile.N - 1)
        for i in range(2 ** profile.M):
            upload_blob(bitmap, "all_windows/window_%d/bitmap_%d" % (i, i))
            upload_blob(bitmap, "all_windows/window_%d/losses_mask_%d" % (i, i))
            # For each fragment in the SCHC Profile, create its blob.

            try:
                _ = requests.post(
                    url=config.CLEAN_WINDOW_URL,
                    json={"header_bytes": header_bytes,
                          "window_number": i,
                          "clear": request_dict["clear"] if "clear" in request_dict else "False"},
                    timeout=0.1)
            except requests.ReadTimeout:
                pass

        if exists_blob("Reassembled_Packet"):
            delete_blob("Reassembled_Packet")

        upload_blob("", "SSN")

        print(f"not_delete_dl_losses? {request_dict['not_delete_dl_losses']}")
        if request_dict["not_delete_dl_losses"] == "False":
            for blob in blob_list():
                if blob.startswith("DL_LOSSES_"):
                    delete_blob(blob)
        else:
            current_experiment = 1
            for blob in blob_list():
                if blob.startswith("DL_LOSSES_"):
                    current_experiment += 1
            print(f"Preparing for the {current_experiment}th experiment")
            upload_blob("", f"DL_LOSSES_{current_experiment}")

        return '', 204


@app.route('/clean_window', methods=['GET', 'POST'])
def clean_window():
    request_dict = request.get_json()
    header_bytes = int(request_dict["header_bytes"])
    window_number = int(request_dict["window_number"])
    profile = Sigfox("UPLINK", "ACK ON ERROR", header_bytes)

    for j in range(2 ** profile.N - 1):
        if request_dict["clear"] == "False":
            upload_blob("", f"all_windows/window_{window_number}/fragment_{window_number}_{j}")
        else:
            delete_blob(f"all_windows/window_{window_number}/fragment_{window_number}_{j}")


if __name__ == "__main__":
    app.run(host='0.0.0.0')
