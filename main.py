import os
import json
import time

from flask import abort
from google.cloud import storage
from math import ceil, floor

from Entities.Fragmenter import Fragmenter
from Entities.Sigfox import Sigfox
from Messages.Fragment import Fragment

from Entities.Reassembler import Reassembler
from Messages.ACK import ACK
from Messages.Fragment import Fragment

from function import *
from blobHelperFunctions import *

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

    # Wait for an HTTP POST request.
    if request.method == 'POST':

        # Get request JSON.
        print("POST RECEIVED")
        request_dict = request.get_json()
        print('Received Sigfox message: {}'.format(request_dict))

        # Get data and Sigfox Sequence Number.
        fragment = request_dict["data"]
        sigfox_sequence_number = request_dict["seqNumber"]

        # Initialize Cloud Storage variables.
        BUCKET_NAME = 'sigfoxschc'

        # Initialize SCHC variables.
        profile_uplink = Sigfox("UPLINK", "ACK ON ERROR")
        profile_downlink = Sigfox("DOWNLINK", "NO ACK")
        buffer_size = profile_uplink.MTU
        n = profile_uplink.N
        m = profile_uplink.M

        # If fragment size is greater than buffer size, ignore it and end function.
        if len(fragment) / 2 * 8 > buffer_size:  # Fragment is hex, 1 hex = 1/2 byte
            return json.dumps({"message": "Fragment size is greater than buffer size D:"}), 200

        # If the folder named "all windows" does not exist, create it along with all subdirectories.
        if not exists_blob(BUCKET_NAME, "all_windows/"):
            print("INITIALIZING... (be patient)")
            create_folder(BUCKET_NAME, "all_windows/")

            # For each window in the SCHC Profile, create its blob.
            for i in range(2 ** m):
                create_folder(BUCKET_NAME, "all_windows/window_%d/" % i)

                # For each fragment in the SCHC Profile, create its blob.
                for j in range(2 ** n - 1):
                    upload_blob(BUCKET_NAME, "", "all_windows/window_%d/fragment_%d_%d" % (i, i, j))

                # Create the blob for each bitmap.
                if not exists_blob(BUCKET_NAME, "all_windows/window_%d/bitmap_%d" % (i, i) or size_blob(BUCKET_NAME, "all_windows/window_%d/bitmap_%d" % (i, i)) == 0):
                    bitmap = ""
                    for b in range(profile_uplink.BITMAP_SIZE):
                        bitmap += "0"
                    upload_blob(BUCKET_NAME, bitmap, "all_windows/window_%d/bitmap_%d" % (i, i))

        print("BLOBs created")

        # Initialize empty window
        window = []
        for i in range(2 ** n - 1):
            window.append([b"", b""])

        # Compute the fragment compressed number (FCN) from the Profile
        fcn_dict = {}
        for j in range(2 ** n - 1):
            fcn_dict[zfill(bin((2 ** n - 2) - (j % (2 ** n - 1)))[2:], 3)] = j

        # Parse fragment into "fragment = [header, payload]
        header = bytes.fromhex(fragment[:2])
        payload = bytearray.fromhex(fragment[2:])
        data = [header, payload]

        # Convert to a Fragment class for easier manipulation.
        fragment_message = Fragment(profile_uplink, data)

        # Get current window for this fragment.
        current_window = int(fragment_message.header.W, 2)

        # Get the current bitmap.
        bitmap = read_blob(BUCKET_NAME, "all_windows/window_%d/bitmap_%d" % (current_window, current_window))

        # Try getting the fragment number from the FCN dictionary.
        try:
            fragment_number = fcn_dict[fragment_message.header.FCN]

            # Check time validation.
            last_time_received = read_blob(BUCKET_NAME, "timestamp")
            time_received = int(request_dict["time"])

            # If this is not the very first fragment and the inactivity timer has been reached, ignore the message. TODO: Send SCHC abort message.
            if str(fragment_number) != "0" and str(current_window) != "0" and time_received - last_time_received > profile_uplink.INACTIVITY_TIMER_VALUE:
                return json.dumps({"message": "Inactivity timer reached. Message ignored."}), 200

            # Upload current timestamp.
            upload_blob(BUCKET_NAME, time_received, "timestamp")

            # Print some data for the user.
            print("[RECV] This corresponds to the " + str(fragment_number) + "th fragment of the " + str(current_window) + "th window.")
            print("[RECV] Sigfox sequence number: " + str(sigfox_sequence_number))

            # Update bitmap and upload it.
            bitmap = replace_bit(bitmap, fragment_number, '1')
            upload_blob(BUCKET_NAME, bitmap, "all_windows/window_%d/bitmap_%d" % (current_window, current_window))

            # Upload the fragment data.
            upload_blob(BUCKET_NAME, data[0].decode("utf-8") + data[1].decode("utf-8"), "all_windows/window_%d/fragment_%d_%d" % (current_window, current_window, fragment_number))

        # If the FCN could not been found, it almost certainly is the final fragment.
        except KeyError:
            print("[RECV] This seems to be the final fragment.")

            # Update bitmap and upload it.
            bitmap = replace_bit(bitmap, len(bitmap) - 1, '1')
            upload_blob(BUCKET_NAME, bitmap, "all_windows/window_%d/bitmap_%d" % (current_window, current_window))

        # Get some SCHC values from the fragment.
        rule_id = fragment_message.header.RULE_ID
        dtag = fragment_message.header.DTAG
        w = fragment_message.header.W

        # Get last and current Sigfox sequence number (SSN)
        if exists_blob(BUCKET_NAME, "SSN"):
            last_sequence_number = read_blob(BUCKET_NAME, "SSN")
        upload_blob(BUCKET_NAME, sigfox_sequence_number, "SSN")

        # If the fragment is at the end of a window (ALL-0 or ALL-1)
        if fragment_message.is_all_0() or fragment_message.is_all_1():

            # Prepare the ACK bitmap.
            for i in range(current_window + 1):
                bitmap_ack = read_blob(BUCKET_NAME, "all_windows/window_%d/bitmap_%d" % (i, i))
                print(bitmap_ack)
                window_ack = i
                if '0' in bitmap_ack:
                    break

            # If the ACK bitmap has a 0 at the end of a non-final window, a fragment has been lost.
            if fragment_message.is_all_0() and '0' in bitmap_ack:
                print("[ALLX] Sending ACK for lost fragments...")

                # Create an ACK message and send it.
                ack = ACK(profile_downlink, rule_id, dtag, zfill(format(window_ack, 'b'), m), bitmap_ack, '0')
                response_json = send_ack(request_dict, ack)
                print("Response content -> {}".format(response_json))
                return response_json, 200

            # If the ACK bitmap is complete and the fragment is an ALL-0, send an ACK
            # This is to be modified, as ACK-on-Error does not need an ACK for every window.
            if fragment_message.is_all_0() and bitmap[0] == '1' and all(bitmap):
                print("[ALLX] Sending ACK after window...")

                # Create an ACK message and send it.
                ack = ACK(profile_downlink, rule_id, dtag, w, bitmap, '0')
                response_json = send_ack(request_dict, ack)
                print("Response content -> {}".format(response_json))
                return response_json, 200

            # If the fragment is an ALL-1
            if fragment_message.is_all_1():

                # Initialize some variables.
                last_index = 0
                last_received_index = 0
                i = 0
                j = 0

                # The next lines are to be remade using the SSNs.

                # Find the index of the first empty blob:
                while i < 2 ** n - 1:

                    # Iterate over the messages until an empty blob is found.
                    if size_blob(BUCKET_NAME, "all_windows/window%d/fragment%d_%d" % (current_window, current_window, i)) == 0:
                        last_index = i
                        break
                    else:
                        i += 1

                # Find the index of the last received fragment.
                while j < 2 ** n - 1:
                    if exists_blob(BUCKET_NAME, "all_windows/window_%d/fragment%d_%d" % (current_window, current_window, j)) and size_blob(BUCKET_NAME, "all_windows/window_%d/fragment%d_%d" % (current_window, current_window, j)) != 0:
                        last_received_index = j + 1
                    j += 1

                # If these indices are not the same, there is a gap between two fragments: a fragment has been lost.
                if last_index != last_received_index:

                    # Send NACK at the end of the window.
                    print("[ALLX] Sending NACK for lost fragments...")
                    ack = ACK(profile_downlink, rule_id, dtag, zfill(format(window_ack, 'b'), m), bitmap_ack, '0')
                    response_json = send_ack(request_dict, ack)
                    return response_json, 200

                # If they are the same, start the reassembling proccess
                else:
                    print("[ALL1] Last fragment. Reassembling...")

                    # Upload the fragment
                    upload_blob(BUCKET_NAME, data[0].decode("utf-8") + data[1].decode("utf-8"), "all_windows/window_%d/fragment_%d_%d" % (current_window, current_window, last_index))

                    # Get all the fragments into an array in the format "fragment = [header, payload]
                    fragments = []
                    for i in range(2 ** m):
                        for j in range(2 ** n - 1):
                            fragment_file = open("./all_windows/window_%d/fragment_%d_%d" % (i, i, j), "r")
                            ultimate_header = fragment_file.read(1)
                            ultimate_payload = fragment_file.read()
                            ultimate_fragment = [ultimate_header.encode(), ultimate_payload.encode()]
                            fragments.append(ultimate_fragment)

                    # Instantiate a Reassembler and start reassembling.
                    reassembler = Reassembler(profile_uplink, fragments)
                    payload = bytearray(reassembler.reassemble())

                    # Upload the full message.
                    upload_blob(BUCKET_NAME, payload.decode("utf-8"), "PAYLOAD")

                    # Send last ACK to end communication.
                    print("[ALL1] Reassembled: Sending last ACK")
                    bitmap = ''
                    for k in range(profile_uplink.BITMAP_SIZE):
                        bitmap += '0'
                    last_ack = ACK(profile_downlink, rule_id, dtag, w, bitmap, '1')
                    response_json = send_ack(request_dict, last_ack)
                    return response_json, 200

        return '', 204

    else:
        print('Invalid HTTP Method to invoke Cloud Function. Only POST supported')
        return abort(405)
