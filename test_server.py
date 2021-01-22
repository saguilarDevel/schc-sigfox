import re
import random

import requests
from flask import Flask, request
import os
import json
from flask import abort, g
import time
from datetime import datetime
from google.cloud import storage
from function import *
from blobHelperFunctions import *
from Entities.Fragmenter import Fragmenter
from Entities.Sigfox import Sigfox
from Messages.Fragment import Fragment

from Entities.Reassembler import Reassembler
from Messages.ACK import ACK
from Messages.Fragment import Fragment
from Messages.ReceiverAbort import ReceiverAbort
from Messages.SenderAbort import SenderAbort

import config.config as config

app = Flask(__name__)

CLIENT_SECRETS_FILE = './credentials/true-sprite-292308-8fa4cf95223b'
# CLIENT_SECRETS_FILE = './credentials/schc-sigfox-upc-f573cd86ed0a.json'

# File where we will store authentication credentials after acquiring them.

CLIENT_SECRETS_FILE = './credentials/WySCHC-Niclabs-7a6d6ab0ca2b.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.CLIENT_SECRETS_FILE

# Filename must be a json file starting with a /
filename = '/fragments_stats_v5.14.json'
filename_dir = os.path.dirname(__file__)
save_path = os.path.join(filename_dir, 'stats', 'files', 'server')

def save_current_fragment(fragment):
    global filename_dir
    global filename
    global save_path
    print("[Save File]: Saving fragment")
    # file = open('fragments_stats.json', 'a+')
    # file.write(json.dumps(fragment))
    # file.write('')
    # file.close()
    data = {}
    try:
        print("[Save File]: Searching for file")
        with open(save_path + filename)  as json_file:
            data = json.load(json_file)
        print("[Save File]: File Found")
    except Exception as e:
        print("[Save File]: Creating file because {}".format(e))
        file = open(save_path + filename, 'a+')
        seqNumber = fragment['seqNumber']
        data[seqNumber] = fragment
        file.write(json.dumps(data))
        file.write('')
        file.close()
        return
    # print("data: {}".format(data))
    # print("fragment: {}".format(fragment))
    # print("fragment['seqNumber']: {}".format(fragment['seqNumber']))
    seqNumber = fragment['seqNumber']
    data[seqNumber] = fragment
    # print("data: {}".format(data))
    file = open(save_path + filename, 'w')
    file.write(json.dumps(data))
    file.write('')
    file.close()
    return


@app.before_request
def before_request():
    g.start = time.time()
    g.current_fragment = {}
    print("datetime: {}".format(datetime.now()))
    if request.endpoint is None:
        print("[before_request]: No request endpoint")
    elif request.endpoint == 'test_link':
        print('[before_request]: ' + request.endpoint)
        if request.method == 'POST':
            request_dict = request.get_json()
            g.current_fragment['timestamp'] = '{}'.format(datetime.now())
            print('[before_request]: Received Sigfox message: {}'.format(request_dict))
            # Get data and Sigfox Sequence Number.
            fragment = request_dict["data"]
            sigfox_sequence_number = request_dict["seqNumber"]
            device = request_dict['device']
            # data = ''.join("{:08b}".format(str(byte)) for byte in bytes(fragment))
            data = bytearray.fromhex(fragment).decode()
            print('fragment: {}'.format(fragment))
            print('data: {}'.format(data))
            print('[before_request]: Data received from device id:{}, data:{}, sigfox_sequence_number:{}'.format(device,
                                                                 request_dict['data'], sigfox_sequence_number))
            g.current_fragment['s-downlink_enable'] = request_dict['ack']
            g.current_fragment['s-sending_start'] = g.start
            g.current_fragment['s-data'] = data
            g.current_fragment['seqNumber'] = sigfox_sequence_number
            g.current_fragment['s-fragment_size'] = len(data)
            print('[before_request]: {}'.format(g.current_fragment))

    elif request.endpoint == 'wyschc_get':
        print('[before_request]: ' + request.endpoint)
        if request.method == 'POST':
            print("[before_request]: POST RECEIVED")
            # BUCKET_NAME = config.BUCKET_NAME
            request_dict = request.get_json()
            print('[before_request]: Received Sigfox message: {}'.format(request_dict))
            # Get data and Sigfox Sequence Number.
            fragment = request_dict["data"]
            sigfox_sequence_number = request_dict["seqNumber"]
            device = request_dict['device']
            print('[before_request]: Data received from device id:{}, data:{}'.format(device, request_dict['data']))
            # Parse fragment into "fragment = [header, payload]
            header_bytes = None
            header_first_hex = fragment[:1]
            if (header_first_hex) == '0' or (header_first_hex) == '1':
                header = bytes.fromhex(fragment[:2])
                payload = bytearray.fromhex(fragment[2:])
                header_bytes = 1
            elif (header_first_hex) == '2':
                header = bytearray.fromhex(fragment[:4])
                payload = bytearray.fromhex(fragment[4:])
                header_bytes = 2
            else:
                print("[before_request]: Wrong header in fragment")
                return 'wrong header', 204

            data = [header, payload]
            # Initialize SCHC variables.
            profile_uplink = Sigfox("UPLINK", "ACK ON ERROR", header_bytes)
            profile_downlink = Sigfox("DOWNLINK", "NO ACK", header_bytes)
            buffer_size = profile_uplink.MTU
            n = profile_uplink.N
            m = profile_uplink.M
            # Convert to a Fragment class for easier manipulation.
            fragment_message = Fragment(profile_uplink, data)

            # Get current window for this fragment.
            current_window = int(fragment_message.header.W, 2)
            # Get some SCHC values from the fragment.
            rule_id = fragment_message.header.RULE_ID
            dtag = fragment_message.header.DTAG
            w = fragment_message.header.W
            g.current_fragment['s-downlink_enable'] = request_dict['ack']
            g.current_fragment['s-sending_start'] = g.start
            g.current_fragment['s-data'] = request_dict["data"]
            g.current_fragment['FCN'] = fragment_message.header.FCN
            g.current_fragment['s-fragment_size'] = len(request_dict["data"])
            g.current_fragment['RULE_ID'] = fragment_message.header.RULE_ID
            g.current_fragment['W'] = fragment_message.header.W
            g.current_fragment['seqNumber'] = sigfox_sequence_number
            print('[before_request]: seqNum:{}, RULE_ID: {} W: {}, FCN: {}'.format(sigfox_sequence_number,
                  fragment_message.header.RULE_ID, fragment_message.header.W, fragment_message.header.FCN))
            print('[before_request]: {}'.format(g.current_fragment))


@app.after_request
def after_request(response):
    diff = time.time() - g.start
    print("[after_request]: execution time: {}".format(diff))
    if request.endpoint == 'wyschc_get':
        g.current_fragment['s-sending_end'] = time.time()
        g.current_fragment['s-send_time'] = diff
        g.current_fragment['s-lost'] = False
        g.current_fragment['s-ack'] = ''
        g.current_fragment['s-ack_send'] = False
        if response.status_code == 204:
            print("[after_request]: response.status_code == 204")
            print(response.get_data())
            if 'fragment lost' in str(response.get_data()):
                print('[after_request]: ups.. fragment lost')
                g.current_fragment['s-lost'] = True

        if response.status_code == 200:
            print("[after_request]: response.status_code == 200")
            response_dict = json.loads(response.get_data())
            print("[after_request]: response_dict: {}".format(response_dict))
            if 'message' in response_dict:
                print(response_dict['message'])
                if 'Message ignored' in response_dict['message']:
                    g.current_fragment['s-ignored'] = True
            else:
                for device in response_dict:
                    print("[after_request]: {}".format(response_dict[device]['downlinkData']))
                    g.current_fragment['s-ack'] = response_dict[device]['downlinkData']
                    g.current_fragment['s-ack_send'] = True

        print('[after_request]: current fragment:{}'.format(g.current_fragment))
        save_current_fragment(g.current_fragment)
        # ack_received
        # sending_end
        # ack
        # send_time

    elif request.endpoint == 'test_link':
        g.current_fragment['s-sending_end'] = time.time()
        g.current_fragment['s-send_time'] = diff
        g.current_fragment['s-ack'] = ''
        g.current_fragment['s-ack_send'] = False
        if response.status_code == 200:
            print("[after_request]: response.status_code == 200")
            response_dict = json.loads(response.get_data())
            print("[after_request]: response_dict: {}".format(response_dict))
            for device in response_dict:
                print("[after_request]: {}".format(response_dict[device]['downlinkData']))
                g.current_fragment['s-ack'] = response_dict[device]['downlinkData']
                g.current_fragment['s-ack_send'] = True
        print('[after_request]: current fragment:{}'.format(g.current_fragment))
        save_current_fragment(g.current_fragment)

    return response


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/test_link', methods=['POST'])
def test_link():
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    import json
    request_json = request.get_json()

    # if request.args and 'device' in request.args:
    #    return request.args.get('message')
    if request_json and 'device' in request_json and 'data' in request_json:
        device = request_json['device']
        print('Data received from device id:{}, data:{}'.format(device, request_json['data']))
        if 'ack' in request_json:
            if request_json['ack'] == 'true':
                response = {request_json['device']: {'downlinkData': '07f7ffffffffffff'}}
                print("response -> {}".format(response))
                return json.dumps(response), 200
        return '', 204
    else:
        return f'Not a correct format message', 404



@app.route('/test', methods=['POST'])
def test():
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    import json
    request_json = request.get_json()

    # if request.args and 'device' in request.args:
    #    return request.args.get('message')
    if request_json and 'device' in request_json and 'data' in request_json:
        device = request_json['device']
        print('Data received from device id:{}, data:{}'.format(device, request_json['data']))
        if 'ack' in request_json:
            if request_json['ack'] == 'true':
                response = {request_json['device']: {'downlinkData': '07f7ffffffffffff'}}
                print("response -> {}".format(response))
                return json.dumps(response), 200
        return '', 204
    else:
        return f'Not a correct format message', 404


global message_number
counter_w0 = 0
counter_w1 = 0


@app.route('/post/message', methods=['GET', 'POST'])
def post_message():
    global counter_w0
    global counter_w1

    if request.method == 'POST':
        print("POST RECEIVED")
        # Get request JSON.
        print("[SCHC-SIGFOX]: POST RECEIVED")
        request_dict = request.get_json()
        print('Received Sigfox message: {}'.format(request_dict))

        # Get data and Sigfox Sequence Number.
        fragment = request_dict["data"]
        sigfox_sequence_number = request_dict["seqNumber"]
        # Parse fragment into "fragment = [header, payload]
        header_bytes = None
        header_first_hex = fragment[:1]
        if (header_first_hex) == '0' or (header_first_hex) == '1':
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
        print('payload: {}'.format(payload))
        data = [header, payload]
        # Initialize SCHC variables.
        profile_uplink = Sigfox("UPLINK", "ACK ON ERROR", header_bytes)
        profile_downlink = Sigfox("DOWNLINK", "NO ACK", header_bytes)
        buffer_size = profile_uplink.MTU
        n = profile_uplink.N
        m = profile_uplink.M
        # Convert to a Fragment class for easier manipulation.
        fragment_message = Fragment(profile_uplink, data)
        # Get some SCHC values from the fragment.
        rule_id = fragment_message.header.RULE_ID
        dtag = fragment_message.header.DTAG
        w = fragment_message.header.W
        print('RULE_ID: {} W: {}, FCN: {}'.format(fragment_message.header.RULE_ID,fragment_message.header.W, fragment_message.header.FCN))
        if fragment_message.is_sender_abort():
            print('sender abort found')
        else:
            print("no sender abort message found")
        if 'ack' in request_dict:
            if request_dict['ack'] == 'true':
                print("sending Receiver Abort message")
                w = ''
                while len(w) < profile_uplink.M:
                    w += '1'
                print("w: {}".format(w))
                abortMessage = ReceiverAbort(profile_downlink, rule_id, dtag)
                print(abortMessage.to_string())
                response_json = send_ack(request_dict, abortMessage)
                # receiverAbort = '0001111111111111111111111111111111111111111111111111111111111111'
                # response = {request_dict['device']: {'downlinkData': receiverAbort}}
                print("response -> {}".format(response_json))
                return response_json, 200

                print('w:{}'.format(w))
                if w == '00':
                    # print('ACK already send for this window, move along')
                    # counter_w0 = 0
                    # return '', 204
                    if counter_w0 == 1:
                        # print('ACK already send for this window, move along')
                        print("This time send an ACK for window 1")
                        counter_w0 = 0
                        bitmap = '0000001'
                        ack = ACK(profile_downlink, rule_id, dtag, "01", bitmap, '0')
                        response_json = send_ack(request_dict, ack)
                        print("200, Response content -> {}".format(response_json))
                        return 'fragment lost', 204
                    counter_w0 += 1
                    print('lets say we lost the All-0, so move along')
                    return 'fragment lost', 204
                    # return str(counter)
                    # Create an ACK message and send it.
                    bitmap = '1011111'
                    bitmap = '1000000'
                    bitmap = '0100001'
                    ack = ACK(profile_downlink, rule_id, dtag, w, bitmap, '1')
                    response_json = send_ack(request_dict, ack)
                    print("200, Response content -> {}".format(response_json))
                    # response = {request_dict['device']: {'downlinkData': '07f7ffffffffffff'}}
                    # print("response -> {}".format(response))
                    return response_json, 200
                elif w == '01':
                    if counter_w1 == 1:

                        print("This time send an ACK for window 1")
                        # counter_w0 = 0
                        counter_w1 += 1
                        bitmap = '0000001'
                        ack = ACK(profile_downlink, rule_id, dtag, "01", bitmap, '0')
                        response_json = send_ack(request_dict, ack)
                        print("200, Response content -> {}".format(response_json))
                        return '', 204

                    elif counter_w1 == 2:
                        print('Resend an ACK for window 1')
                        counter_w1 += 1
                        bitmap = '0000001'
                        ack = ACK(profile_downlink, rule_id, dtag, w, bitmap, '0')
                        response_json = send_ack(request_dict, ack)
                        print("200, Response content -> {}".format(response_json))
                        # response = {request_dict['device']: {'downlinkData': '07f7ffffffffffff'}}
                        # print("response -> {}".format(response))
                        return response_json, 200

                    elif counter_w1 == 3:
                        print('ACK already send for this window, send last ACK')
                        counter_w1 = 0
                        bitmap = '0100001'
                        ack = ACK(profile_downlink, rule_id, dtag, w, bitmap, '1')
                        response_json = send_ack(request_dict, ack)
                        print("200, Response content -> {}".format(response_json))
                        # response = {request_dict['device']: {'downlinkData': '07f7ffffffffffff'}}
                        # print("response -> {}".format(response))
                        return response_json, 200


                        bitmap = '0100001'
                        ack = ACK(profile_downlink, rule_id, dtag, w, bitmap, '1')
                        response_json = send_ack(request_dict, ack)
                        print("200, Response content -> {}".format(response_json))
                    counter_w1 += 1
                    # Create an ACK message and send it.
                    bitmap = '0000001'

                    ack = ACK(profile_downlink, rule_id, dtag, w, bitmap, '0')

                    # Test for loss of All-0 in window 0
                    bitmap = '1010110'
                    ack = ACK(profile_downlink, rule_id, dtag, '00', bitmap, '0')
                    # ack = ACK(profile_downlink, rule_id, dtag, w, bitmap, '1')
                    response_json = send_ack(request_dict, ack)
                    print("200, Response content -> {}".format(response_json))
                    # response = {request_dict['device']: {'downlinkData': '07f7ffffffffffff'}}
                    # print("response -> {}".format(response))
                    return response_json, 200
                else:
                    return '', 204
            return '', 204
        else:
            return f'Not a correct format message', 404


@app.route('/hello_get', methods=['GET', 'POST'])
def hello_get():
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

@app.route('/clean', methods=['GET', 'POST'])
def clean():
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
        print("[Clean]: POST RECEIVED")
        BUCKET_NAME = config.BUCKET_NAME
        request_dict = request.get_json()
        print('[Clean]: Received Request message: {}'.format(request_dict))
        header_bytes = int(request_dict["header_bytes"])
        profile = Sigfox("UPLINK", "ACK ON ERROR", header_bytes)
        bitmap = ''
        for i in range(2**profile.N - 1):
            bitmap += '0'
        for i in range(2**profile.M):
            upload_blob(BUCKET_NAME, bitmap, "all_windows/window_%d/bitmap_%d" % (i, i))
            upload_blob(BUCKET_NAME, bitmap, "all_windows/window_%d/losses_mask_%d" % (i, i))
        print("[Clean]: Clean completed")

        return '', 204

@app.route('/losses_mask', methods=['GET', 'POST'])
def losses_mask():
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
        header_bytes = int(request_dict["header_bytes"])
        profile = Sigfox("UPLINK", "ACK ON ERROR", header_bytes)
        for i in range(2**profile.M):
            upload_blob(BUCKET_NAME, mask, "all_windows/window_%d/losses_mask_%d" % (i,i))

        return '', 204

@app.route('/wyschc_get', methods=['GET', 'POST'])
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

    # Wait for an HTTP POST request.
    if request.method == 'POST':

        # Get request JSON.
        print("[SCHC-SIGFOX]: POST RECEIVED")
        request_dict = request.get_json()
        print('Received Sigfox message: {}'.format(request_dict))

        # Get data and Sigfox Sequence Number.
        fragment = request_dict["data"]
        sigfox_sequence_number = request_dict["seqNumber"]

        # Initialize Cloud Storage variables.

        # BUCKET_NAME = 'sigfoxschc'
        # BUCKET_NAME = 'wyschc-niclabs'
        BUCKET_NAME = config.BUCKET_NAME

        # Parse fragment into "fragment = [header, payload]
        header_bytes = None
        header_first_hex = fragment[:1]
        if (header_first_hex) == '0' or (header_first_hex) == '1':
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
                if not exists_blob(BUCKET_NAME, "all_windows/window_%d/bitmap_%d" % (i, i) or size_blob(BUCKET_NAME, "all_windows/window_%d/bitmap_%d" % (i, i)) == 0):
                    bitmap = ""
                    for b in range(profile_uplink.BITMAP_SIZE):
                        bitmap += "0"
                    upload_blob(BUCKET_NAME, bitmap, "all_windows/window_%d/bitmap_%d" % (i, i))

        if not exists_blob(BUCKET_NAME, "timestamp"):
            upload_blob(BUCKET_NAME, request_dict["time"], "timestamp")

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

        # Get current window for this fragment.
        current_window = int(fragment_message.header.W, 2)

        # Get the current bitmap.
        bitmap = read_blob(BUCKET_NAME, "all_windows/window_%d/bitmap_%d" % (current_window, current_window))

        if 'enable_losses' in request_dict and not(fragment_message.is_all_0() or fragment_message.is_all_1()):
            if request_dict['enable_losses']:
                loss_rate = request_dict["loss_rate"]
                # loss_rate = 10
                coin = random.random()
                print('loss rate: {}, random toss:{}'.format(loss_rate, coin * 100))
                if coin * 100 < loss_rate:
                    print("[LOSS] The fragment was lost.")
                    return 'fragment lost', 204

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

            # Update bitmap and upload it.
            bitmap = replace_bit(bitmap, fragment_number, '1')
            upload_blob(BUCKET_NAME, bitmap, "all_windows/window_%d/bitmap_%d" % (current_window, current_window))

            # Upload the fragment data.
            upload_blob_using_threads(BUCKET_NAME, data[0].decode("utf-8") + data[1].decode("utf-8"),
                                      "all_windows/window_%d/fragment_%d_%d" % (
                                          current_window, current_window, fragment_number))

        # If the FCN could not been found, it almost certainly is the final fragment.
        except KeyError:
            print("[RECV] This seems to be the final fragment.")

            # Update bitmap and upload it.
            bitmap = replace_bit(bitmap, len(bitmap) - 1, '1')
            upload_blob_using_threads(BUCKET_NAME, bitmap,
                                      "all_windows/window_%d/bitmap_%d" % (current_window, current_window))

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
                print("[ALL0] Sending ACK for lost fragments...")
                print("bitmap with errors -> {}".format(bitmap_ack))
                # Create an ACK message and send it.
                ack = ACK(profile_downlink, rule_id, dtag, zfill(format(window_ack, 'b'), m), bitmap_ack, '0')
                response_json = send_ack(request_dict, ack)
                print("Response content -> {}".format(response_json))
                return response_json, 200

            # If the ACK bitmap is complete and the fragment is an ALL-0, send an ACK
            # This is to be modified, as ACK-on-Error does not need an ACK for every window.
            # No need to send an ACK if the bitmap has all 1.
            if fragment_message.is_all_0() and bitmap[0] == '1' and all(bitmap):
                print("[ALL0] No ACK sent after intermediate window...")

                # Create an ACK message and send it.
                # ack = ACK(profile_downlink, rule_id, dtag, w, bitmap, '0')
                # response_json = send_ack(request_dict, ack)
                print("204, Response content -> ''")
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
                pattern = re.compile("1*0*1")

                # If the bitmap matches the regex, check if the last two received fragments are consecutive.
                if pattern.fullmatch(bitmap):
                    # If the last two received fragments are consecutive, accept the ALL-1 and start reassembling
                    if int(sigfox_sequence_number) - int(last_sequence_number) == 1:

                        last_index = int(read_blob(BUCKET_NAME, "fragment_number")) + 1
                        upload_blob_using_threads(BUCKET_NAME, data[0].decode("utf-8") + data[1].decode("utf-8"),
                                                  "all_windows/window_%d/fragment_%d_%d" % (
                                                      current_window, current_window, last_index))
                        try:
                            _ = requests.post(url='http://localhost:5000/http_reassemble', json={"last_index": last_index, "current_window": current_window, "header_bytes": header_bytes}, timeout=1)
                        except requests.exceptions.ReadTimeout:
                            pass

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
                        # Send NACK at the end of the window.
                        print("[ALLX] Sending NACK for lost fragments...")
                        ack = ACK(profile_downlink, rule_id, dtag, zfill(format(window_ack, 'b'), m), bitmap_ack, '0')
                        response_json = send_ack(request_dict, ack)
                        return response_json, 200

                    # If they are not, there is a gap between two fragments: a fragment has been lost.
                # The same happens if the bitmap doesn't match the regex.
                else:
                    # Send NACK at the end of the window.
                    print("[ALLX] Sending NACK for lost fragments...")
                    ack = ACK(profile_downlink, rule_id, dtag, zfill(format(window_ack, 'b'), m), bitmap_ack, '0')
                    response_json = send_ack(request_dict, ack)
                    return response_json, 200

        return '', 204

    else:
        print('Invalid HTTP Method to invoke Cloud Function. Only POST supported')
        return abort(405)


@app.route('/http_reassemble', methods=['GET', 'POST'])
def http_reassemble():
    if request.method == "POST":

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
        print("[REASSEMBLE] current_window: {}".format(current_window))
        print("[REASSEMBLE] last_index: {}".format(last_index))


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
        upload_blob_using_threads(BUCKET_NAME, payload.decode("utf-8"), "PAYLOAD")
        try:
            _ = requests.post(url='http://localhost:5000/clean',
                              json={"header_bytes": header_bytes}, timeout=1)
        except requests.exceptions.ReadTimeout:
            pass
        return '', 204


if __name__ == "__main__":
    app.run(host='0.0.0.0')
