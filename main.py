import re
import time
import random
import requests

from flask import abort
from Entities.Sigfox import Sigfox

from Entities.Reassembler import Reassembler
from Messages.ACK import ACK
from Messages.Fragment import Fragment

from function import *
from blobHelperFunctions import *
import config.config as config

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
        BUCKET_NAME = config.BUCKET_NAME

        # Parse fragment into "fragment = [header, payload]
        header_bytes = None
        header_first_hex = fragment[:1]
        if (header_first_hex) == '0' or (header_first_hex) =='1':
            header = bytes.fromhex(fragment[:2])
            payload = bytearray.fromhex(fragment[2:])
            header_bytes = 1
        elif (header_first_hex) == '2':
            header = bytearray.fromhex(fragment[:4])
            payload = bytearray.fromhex(fragment[4:])
            header_bytes = 2
        else:
            print("Wrong header in fragment")
            return 'wrong header', 204

        if bytearray.fromhex(fragment).decode() == "CLEAN":
            t_i = time.perf_counter()
            _ = requests.post(
                url='https://southamerica-east1-wyschc-303621.cloudfunctions.net/clean',
                json={"header_bytes": header_bytes})
            t_f = (time.perf_counter())
            print("[PERF] Cleanup took {} seconds".format(t_f - t_i))
            return '', 204

        data = [header, payload]

        # Initialize SCHC variables.
        profile_uplink = Sigfox("UPLINK", "ACK ON ERROR", header_bytes)
        profile_downlink = Sigfox("DOWNLINK", "NO ACK", header_bytes)
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
                if not exists_blob(BUCKET_NAME, "all_windows/window_%d/bitmap_%d" % (i, i) or size_blob(BUCKET_NAME,
                                                                                                        "all_windows/window_%d/bitmap_%d" % (
                                                                                                        i, i)) == 0):
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
            fcn_dict[zfill(bin((2 ** n - 2) - (j % (2 ** n - 1)))[2:], n)] = j


        # Convert to a Fragment class for easier manipulation.
        fragment_message = Fragment(profile_uplink, data)

        if 'enable_losses' in request_dict:
            if request_dict['enable_losses']:
                loss_rate = request_dict["loss_rate"]
                # loss_rate = 10
                coin = random.random()
                print('loss rate: {}, random toss:{}'.format(loss_rate, coin * 100))
                if coin * 100 < loss_rate:
                    print("[LOSS] The fragment was lost.")
                    if fragment_message.is_all_1():
                        last_sequence_number = read_blob(BUCKET_NAME, "SSN")
                        print("SSN is {} and last SSN is {}".format(sigfox_sequence_number, last_sequence_number))
                        if int(sigfox_sequence_number) - int(last_sequence_number) == 1:
                            # We do that to save the last SSN value for future use (when the next All-1 Arrives)
                            # In a Real Loss Scenario we will not know the SSN...
                            upload_blob(BUCKET_NAME, sigfox_sequence_number, "SSN")
                    return 'fragment lost', 204

        # Get current window for this fragment.
        current_window = int(fragment_message.header.W, 2)

        # Get the current bitmap.
        bitmap = read_blob(BUCKET_NAME, "all_windows/window_%d/bitmap_%d" % (current_window, current_window))

        # Try getting the fragment number from the FCN dictionary.
        try:
            fragment_number = fcn_dict[fragment_message.header.FCN]
            upload_blob(BUCKET_NAME, fragment_number, "fragment_number")

            time_received = int(request_dict["time"])
            if exists_blob(BUCKET_NAME, "timestamp"):
                # Check time validation.
                last_time_received = int(read_blob(BUCKET_NAME, "timestamp"))

                # If this is not the very first fragment and the inactivity timer has been reached, ignore the message.
                # TODO: Send SCHC abort message.
                if str(fragment_number) != "0" and str(
                        current_window) != "0" and time_received - last_time_received > profile_uplink.INACTIVITY_TIMER_VALUE:
                    return json.dumps({"message": "Inactivity timer reached. Message ignored."}), 200

            # Upload current timestamp.
            upload_blob(BUCKET_NAME, time_received, "timestamp")

            # Print some data for the user.
            print("[RECV] This corresponds to the " + str(fragment_number) + "th fragment of the " + str(
                current_window) + "th window.")
            print("[RECV] Sigfox sequence number: " + str(sigfox_sequence_number))

            #Controlled Errors check
            # losses_mask = read_blob(BUCKET_NAME, "all_windows/window_%d/losses_mask_%d" % (current_window, current_window))
            # if (losses_mask[fragment_number]) != '0':
            #     losses_mask = replace_bit(losses_mask, fragment_number, str(int(losses_mask[fragment_number])-1))
            #     upload_blob(BUCKET_NAME, losses_mask, "all_windows/window_%d/losses_mask_%d" % (current_window, current_window))
            #     print("[LOSS] The fragment was lost.")
            #     return 'fragment lost', 204

            # Update bitmap and upload it.
            bitmap = replace_bit(bitmap, fragment_number, '1')
            upload_blob(BUCKET_NAME, bitmap, "all_windows/window_%d/bitmap_%d" % (current_window, current_window))

            # Upload the fragment data.
            upload_blob(BUCKET_NAME, data[0].decode("ISO-8859-1") + data[1].decode("utf-8"),
                        "all_windows/window_%d/fragment_%d_%d" % (current_window, current_window, fragment_number))

        # If the FCN could not been found, it almost certainly is the final fragment.
        except KeyError:
            print("[RECV] This seems to be the final fragment.")
            # Upload current timestamp.
            time_received = int(request_dict["time"])
            upload_blob(BUCKET_NAME, time_received, "timestamp")
            print("is All-1:{}, is All-0:{}".format(fragment_message.is_all_1(), fragment_message.is_all_0()))
            # print("RULE_ID: {}, W:{}, FCN:{}".format(fragment.header.RULE_ID, fragment.header.W, fragment.header.FCN))
            # Update bitmap and upload it.
            bitmap = replace_bit(bitmap, len(bitmap) - 1, '1')
            upload_blob(BUCKET_NAME, bitmap, "all_windows/window_%d/bitmap_%d" % (current_window, current_window))

        # Get some SCHC values from the fragment.
        rule_id = fragment_message.header.RULE_ID
        dtag = fragment_message.header.DTAG
        w = fragment_message.header.W

        # Get last and current Sigfox sequence number (SSN)
        last_sequence_number = 0
        if exists_blob(BUCKET_NAME, "SSN"):
            last_sequence_number = read_blob(BUCKET_NAME, "SSN")
        upload_blob(BUCKET_NAME, sigfox_sequence_number, "SSN")

        # If the fragment is at the end of a window (ALL-0 or ALL-1)
        if fragment_message.is_all_0() or fragment_message.is_all_1():

            # Prepare the ACK bitmap. Find the first bitmap with a 0 in it.
            for i in range(current_window + 1):
                bitmap_ack = read_blob(BUCKET_NAME, "all_windows/window_%d/bitmap_%d" % (i, i))
                print(bitmap_ack)
                window_ack = i
                if '0' in bitmap_ack:
                    break

            # If the ACK bitmap has a 0 at the end of a non-final window, a fragment has been lost.
            if fragment_message.is_all_0() and '0' in bitmap_ack:
                if 'enable_dl_losses' in request_dict:
                    if request_dict['enable_dl_losses']:
                        coin = random.random()
                        print('loss rate: {}, random toss:{}'.format(loss_rate, coin * 100))
                        if coin * 100 < loss_rate:
                            print("[LOSS-ALL0] The Downlink NACK was lost.")
                            upload_blob(BUCKET_NAME, read_blob(BUCKET_NAME, "DL_LOSSES") + "\n Lost DL message in window {}".format(current_window), "DL_LOSSES")
                            return 'Downlink lost', 204
                print("[ALL0] Sending ACK for lost fragments...")
                print("bitmap with errors -> {}".format(bitmap_ack))
                # Create an ACK message and send it.
                ack = ACK(profile_downlink, rule_id, dtag, zfill(format(window_ack, 'b'), m), bitmap_ack, '0')
                response_json = send_ack(request_dict, ack)
                print("Response content -> {}".format(response_json))
                return response_json, 200

            # If the ACK bitmap is complete and the fragment is an ALL-0, send an ACK
            # This is to be modified, as ACK-on-Error does not need an ACK for every window.
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
                # response = {request_dict['device']: {'downlinkData': '080fffffffffffff'}}
                # print("response -> {}".format(json.dumps(response)))
                # return json.dumps(response), 200
                # The bitmap in the last window follows the following regular expression: "1*0*1*"
                # Since the ALL-1, if received, changes the least significant bit of the bitmap.
                # For a "complete" bitmap in the last window, there shouldn't be non-consecutive zeroes:
                # 1110001 is a valid bitmap, 1101001 is not.

                pattern2 = re.compile("0*1")
                if pattern2.fullmatch(bitmap_ack):
                    if 'enable_dl_losses' in request_dict:
                        if request_dict['enable_dl_losses']:
                            coin = random.random()
                            print('loss rate: {}, random toss:{}'.format(loss_rate, coin * 100))
                            if coin * 100 < loss_rate:
                                print("[LOSS-ALL1] The Downlink ACK was lost.")
                                upload_blob(BUCKET_NAME, read_blob(BUCKET_NAME, "DL_LOSSES") + "\n Lost DL message in window {}".format(current_window), "DL_LOSSES")
                                return 'Downlink lost', 204
                    print("SSN is {} and last SSN is {}".format(sigfox_sequence_number, last_sequence_number))
                    # Downlink Controlled Errors
                    dl_errors = int(read_blob(BUCKET_NAME, "dl_errors"))
                    if dl_errors == 0:
                        last_index = 0
                        upload_blob(BUCKET_NAME, data[0].decode("ISO-8859-1") + data[1].decode("utf-8"),
                                    "all_windows/window_%d/fragment_%d_%d" % (
                                        current_window, current_window, last_index))
                        print("Info for reassemble: last_index:{}, current_window:{}".format(last_index, current_window))
                        try:
                            print('Activating reassembly process...')
                            _ = requests.post(
                                url='https://europe-west1-true-sprite-292308.cloudfunctions.net/http_reassemble',
                                json={"last_index": last_index, "current_window": current_window,
                                      "header_bytes": header_bytes},
                                timeout=0.0000000001)
                        # except requests.exceptions.ReadTimeout:
                        #     pass
                        except Exception as e:
                            print("exception in reassembly call: {}".format(e))

                        # Send last ACK to end communication.
                        print("[ALL1] Reassembled: Sending last ACK")
                        bitmap = ''
                        for k in range(profile_uplink.BITMAP_SIZE):
                            bitmap += '0'
                        last_ack = ACK(profile_downlink, rule_id, dtag, w, bitmap, '1')
                        response_json = send_ack(request_dict, last_ack)
                        # return response_json, 200
                        # response_json = send_ack(request_dict, last_ack)
                        print("200, Response content -> {}".format(response_json))
                        return response_json, 200
                    else:
                        dl_errors -= 1
                        upload_blob(BUCKET_NAME, dl_errors, "dl_errors")
                        print("[DL-ERROR] We simulate a downlink error. We don't send an ACK")
                        return '', 204

                pattern = re.compile("1*0*1")

                # If the bitmap matches the regex, check if the last two received fragments are consecutive.
                if pattern.fullmatch(bitmap_ack):
                    print("SSN is {} and last SSN is {}".format(sigfox_sequence_number,last_sequence_number))
                    # If the last two received fragments are consecutive, accept the ALL-1 and start reassembling
                    if 'enable_dl_losses' in request_dict:
                        if request_dict['enable_dl_losses']:
                            coin = random.random()
                            print('loss rate: {}, random toss:{}'.format(loss_rate, coin * 100))
                            if coin * 100 < loss_rate:
                                print("[LOSS-ALL1] The Downlink ACK was lost.")
                                upload_blob(BUCKET_NAME, read_blob(BUCKET_NAME, "DL_LOSSES") + "\n Lost DL message in window {}".format(current_window), "DL_LOSSES")
                                return 'Downlink lost', 204
                    if int(sigfox_sequence_number) - int(last_sequence_number) == 1:
                        # Downlink Controlled Errors
                        dl_errors = int(read_blob(BUCKET_NAME, "dl_errors"))
                        if dl_errors == 0:
                            last_index = int(read_blob(BUCKET_NAME, "fragment_number")) + 1
                            upload_blob(BUCKET_NAME, data[0].decode("ISO-8859-1") + data[1].decode("utf-8"),
                                        "all_windows/window_%d/fragment_%d_%d" % (
                                            current_window, current_window, last_index))
                            print("Info for reassemble: last_index:{}, current_window:{}".format(last_index,current_window))
                            try:
                                print('Activating reassembly process...')
                                _ = requests.post(url='https://europe-west1-true-sprite-292308.cloudfunctions.net/http_reassemble',
                                                  json={"last_index": last_index, "current_window": current_window, "header_bytes": header_bytes},
                                                  timeout=0.0000000001)
                            # except requests.exceptions.ReadTimeout:
                            #     pass
                            except Exception as e:
                                print("exception in reassembly call: {}".format(e))

                            # Send last ACK to end communication.
                            print("[ALL1] Reassembled: Sending last ACK")
                            bitmap = ''
                            for k in range(profile_uplink.BITMAP_SIZE):
                                bitmap += '0'
                            last_ack = ACK(profile_downlink, rule_id, dtag, w, bitmap, '1')
                            response_json = send_ack(request_dict, last_ack)
                            # return response_json, 200
                            # response_json = send_ack(request_dict, last_ack)
                            print("200, Response content -> {}".format(response_json))
                            return response_json, 200
                        else:
                            dl_errors -= 1
                            upload_blob(BUCKET_NAME, dl_errors, "dl_errors")
                            print("[DL-ERROR] We simulate a downlink error. We don't send an ACK")
                            return '', 204
                    else:
                        # Send NACK at the end of the window.
                        if 'enable_dl_losses' in request_dict:
                            if request_dict['enable_dl_losses']:
                                coin = random.random()
                                print('loss rate: {}, random toss:{}'.format(loss_rate, coin * 100))
                                if coin * 100 < loss_rate:
                                    print("[LOSS-ALL1] The Downlink NACK was lost.")
                                    upload_blob(BUCKET_NAME, read_blob(BUCKET_NAME, "DL_LOSSES") + "\n Lost DL message in window {}".format(current_window), "DL_LOSSES")
                                    return 'Downlink lost', 204
                        print("[ALLX] Sending NACK for lost fragments because of SSN...")
                        ack = ACK(profile_downlink, rule_id, dtag, zfill(format(window_ack, 'b'), m), bitmap_ack, '0')
                        response_json = send_ack(request_dict, ack)
                        return response_json, 200

                    # If they are not, there is a gap between two fragments: a fragment has been lost.
                # The same happens if the bitmap doesn't match the regex.
                else:
                    # Send NACK at the end of the window.
                    if 'enable_dl_losses' in request_dict:
                        if request_dict['enable_dl_losses']:
                            coin = random.random()
                            print('loss rate: {}, random toss:{}'.format(loss_rate, coin * 100))
                            if coin * 100 < loss_rate:
                                print("[LOSS-ALL1] The Downlink NACK was lost.")
                                upload_blob(BUCKET_NAME, read_blob(BUCKET_NAME, "DL_LOSSES") + "\n Lost DL message in window {}".format(current_window), "DL_LOSSES")
                                return 'Downlink lost', 204
                    print("[ALLX] Sending NACK for lost fragments...")
                    ack = ACK(profile_downlink, rule_id, dtag, zfill(format(window_ack, 'b'), m), bitmap_ack, '0')
                    response_json = send_ack(request_dict, ack)
                    return response_json, 200

        return '', 204

    else:
        print('Invalid HTTP Method to invoke Cloud Function. Only POST supported')
        return abort(405)


def http_reassemble(request):

    # Wait for an HTTP POST request.
    if request.method == 'POST':

        # Get request JSON.
        print("[REASSEMBLE] POST RECEIVED")
        request_dict = request.get_json()
        print('Received HTTP message: {}'.format(request_dict))

        current_window = int(request_dict["current_window"])
        last_index = int(request_dict["last_index"])
        header_bytes = int(request_dict["header_bytes"])

        # Initialize Cloud Storage variables.
        # BUCKET_NAME = 'sigfoxschc'
        # BUCKET_NAME = 'wyschc-niclabs'
        BUCKET_NAME = config.BUCKET_NAME

        # Initialize SCHC variables.
        profile_uplink = Sigfox("UPLINK", "ACK ON ERROR", header_bytes)
        n = profile_uplink.N
        # Find the index of the first empty blob:

        print("[REASSEMBLE] Reassembling...")

        # Get all the fragments into an array in the format "fragment = [header, payload]"
        fragments = []

        # TODO: This assumes that the last received message is in the last window.
        for i in range(current_window + 1):
            for j in range(2 ** n - 1):
                print("Loading fragment {}".format(j))
                fragment_file = read_blob(BUCKET_NAME,
                                          "all_windows/window_%d/fragment_%d_%d" % (i, i, j))
                print(fragment_file)
                ultimate_header = fragment_file[:header_bytes]
                ultimate_payload = fragment_file[header_bytes:]
                ultimate_fragment = [ultimate_header.encode(), ultimate_payload.encode()]
                fragments.append(ultimate_fragment)
                if i == current_window and j == last_index:
                    break

        # Instantiate a Reassembler and start reassembling.
        reassembler = Reassembler(profile_uplink, fragments)
        payload = bytearray(reassembler.reassemble())

        # Upload the full message.
        upload_blob(BUCKET_NAME, payload.decode("utf-8"), "Reassembled_Packet")

        return '', 204

def losses_mask(request):
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
        BUCKET_NAME = config.BUCKET_NAME
        request_dict = request.get_json()
        print('Received Request message: {}'.format(request_dict))
        mask = request_dict["mask"]
        last_error_window = int(request_dict["last_error_window"])
        for i in range(last_error_window+1):
            upload_blob(BUCKET_NAME, mask, "all_windows/window_%d/losses_mask_%d" % (i,i))

        return '', 204

def clean(request):
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
        header_bytes = int(request_dict["header_bytes"])
        profile = Sigfox("UPLINK", "ACK ON ERROR", header_bytes)
        bitmap = ''
        BUCKET_NAME = config.BUCKET_NAME
        for i in range(2 ** profile.N - 1):
            bitmap += '0'
        for i in range(2 ** profile.M):
            upload_blob(BUCKET_NAME, bitmap, "all_windows/window_%d/bitmap_%d" % (i, i))
            upload_blob(BUCKET_NAME, bitmap, "all_windows/window_%d/losses_mask_%d" % (i, i))
        if exists_blob(BUCKET_NAME, "Reassembled_message"):
            delete_blob(BUCKET_NAME, "Reassembled_message")
        upload_blob(BUCKET_NAME, "", "DL_LOSSES")
        return '', 204