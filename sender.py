import json
import time

import requests
from requests import Timeout

from Entities.Fragmenter import Fragmenter
from Entities.Sigfox import Sigfox
from Messages.Fragment import Fragment
from Messages.SenderAbort import SenderAbort
from function import zfill

filename = "example.txt"
seqNumber = 1
device = "4D5A87"
enable_losses = False


def post(fragment_sent, retransmit=False):
    global seqNumber, attempts, current_window, last_window, i
    url = "http://localhost:5000/wyschc_get"
    headers = {'content-type': 'application/json'}
    profile = fragment_sent.profile

    if fragment_sent.is_all_0():
        print("[POST] This is an All-0. Using All-0 SIGFOX_DL_TIMEOUT Timeout.")
        request_timeout = profile.SIGFOX_DL_TIMEOUT
    elif fragment_sent.is_all_1():
        print("[POST] This is an All-1. Using RETRANSMISSION_TIMER_VALUE. Increasing ACK attempts.")
        attempts += 1
        request_timeout = profile.RETRANSMISSION_TIMER_VALUE
    else:
        request_timeout = 45

    payload_dict = {
        "deviceType": "WYSCHC",
        "device": device,
        "time": str(int(time.time())),
        "data": fragment_sent.hex,
        "seqNumber": str(seqNumber),
        "ack": fragment_sent.expects_ack()
    }

    if enable_losses:
        print("Losses are enabled")
        payload_dict = {**payload_dict, **{"enable_losses": enable_losses}}

    print(f"[POST] Posting fragment {fragment_sent.hex} to {url}")

    try:
        response = requests.post(url, data=json.dumps(payload_dict), headers=headers, timeout=request_timeout)

        if fragment_sent.is_sender_abort():
            print("Sent Sender-Abort. Goodbye")
            exit(1)

        seqNumber += 1
        print(f"[POST] Response: {response}")
        http_code = response.status_code

        # If 500, exit with an error
        if http_code == 500:
            print("Response: 500 Internal Server Error")
            exit(1)

        # If 204, the fragment was posted successfully
        elif http_code == 204:
            print("Response: 204 No Content")
            if not retransmit:
                i += 1

        # If 200, the fragment was posted and an ACK has been received.
        elif http_code == 200:
            print(f"Response: 200 OK, Text: {response.text}. Ressetting attempts counter to 0.")
            attempts = 0
            ack = response.json()[device]["downlinkData"]

            if not fragment_sent.expects_ack():
                print(f"ERROR: ACK received but not requested ({ack}).")
                exit(1)

            # Extracting data from the ACK
            ack = zfill(bin(int(ack, 16))[2:], 64)
            ack_window = int(ack[ack_index_w:ack_index_c], 2)
            c = ack[ack_index_c]
            bitmap = ack[ack_index_bitmap:ack_index_padding]
            print(f"ACK: {ack}")
            print(f"ACK window: {str(ack_window)}")
            print(f"ACK bitmap: {bitmap}")
            print(f"ACK C bit: {c}")

            # If the W field in the SCHC ACK corresponds to the last window of the SCHC Packet:
            if ack_window == last_window:
                # If the C bit is set, the sender MAY exit successfully.
                if c == '1':
                    print("Last ACK received, fragments reassembled successfully. End of transmission.")
                    exit(0)
                # Otherwise,
                else:
                    # If the Profile mandates that the last tile be sent in an All-1 SCHC Fragment
                    # (we are in the last window), .is_all_1() should be true:
                    if fragment_sent.is_all_1():
                        # This is the last bitmap, it contains the data up to the All-1 fragment.
                        last_bitmap = bitmap[:len(fragment_list) % profile_uplink.WINDOW_SIZE + 1]

                        # If the SCHC ACK shows no missing tile at the receiver, abort.
                        # (C = 0 but transmission complete)
                        if last_bitmap[0] == '1' and all(last_bitmap):
                            print("ERROR: SCHC ACK shows no missing tile at the receiver.")
                            post(SenderAbort(fragment_sent.profile, fragment_sent.header))

                        # Otherwise (fragments are lost),
                        else:
                            # Check for lost fragments.
                            for j in range(len(last_bitmap)):
                                # If the j-th bit of the bitmap is 0, then the j-th fragment was lost.
                                if last_bitmap[j] == '0':
                                    print(f"The {str(j)}th ({str((2 ** profile_uplink.N - 1) * ack_window + j)} / {str(len(fragment_list))}) fragment was lost! Sending again...")
                                    # Try sending again the lost fragment.
                                    fragment_to_be_resent = Fragment(profile_uplink, fragment_list[(2 ** profile_uplink.N - 1) * ack_window + j])
                                    print(f"Lost fragment: {fragment_to_be_resent.string}")
                                    post(fragment_to_be_resent, retransmit=True)

                                    # If the last of these SCHC fragments is not an All-1, send an ACK REQ with
                                    # the W field of the last window. This is to be reviewed, as the Sigfox draft
                                    # does not specify this.
                                    # if j == len(bitmap) + 1 and not fragment_to_be_resent.is_all_1():
                                    #   ackreq = generate_ack_req(fragment)
                                    #   post(ackreq)
                    else:
                        print("ERROR: While being at the last window, the ACK-REQ was not an All-1."
                              "This is outside of the Sigfox scope.")
                        exit(1)

            # Otherwise, there are lost fragments in a non-final window.
            else:
                # Check for lost fragments.
                for j in range(len(bitmap)):
                    # If the j-th bit of the bitmap is 0, then the j-th fragment was lost.
                    if bitmap[j] == '0':
                        print(f"The {str(j)}th ({str((2 ** profile_uplink.N - 1) * ack_window + j)} / {str(len(fragment_list))}) fragment was lost! Sending again...")
                        # Try sending again the lost fragment.
                        fragment_to_be_resent = Fragment(profile_uplink, fragment_list[(2 ** profile_uplink.N - 1) * ack_window + j])
                        print(f"Lost fragment: {fragment_to_be_resent.string}")
                        post(fragment_to_be_resent, retransmit=True)

    # If the timer expires
    except Timeout:
        # If an ACK was expected
        if fragment_sent.is_all_1():
            # If the attempts counter is strictly less than MAX_ACK_REQUESTS, try again
            if attempts < profile_uplink.MAX_ACK_REQUESTS:
                print("SCHC Timeout reached while waiting for an ACK. Sending the ACK Request again...")
                post(fragment_sent)
            # Else, exit with an error.
            else:
                print("ERROR: MAX_ACK_REQUESTS reached. Sending Sender-Abort.")
                header = fragment_sent.header
                abort = SenderAbort(profile, header)
                post(abort)

        # If the ACK can be not sent (Sigfox only)
        if fragment_sent.is_all_0():
            print("All-0 timeout reached. Proceeding to next window.")
            if not retransmit:
                i += 1
                current_window += 1

        # Else, HTTP communication failed.
        else:
            print("ERROR: HTTP Timeout reached.")
            exit(1)


# Read the file to be sent.
with open(filename, "rb") as data:
    f = data.read()
    message = bytearray(f)

# Initialize variables.
total_size = len(message)
current_size = 0
percent = round(0, 2)
i = 0
current_window = 0
profile_uplink = Sigfox("UPLINK", "ACK ON ERROR", header_bytes=1)
profile_downlink = Sigfox("DOWNLINK", "NO ACK", header_bytes=1)

ack_index_dtag = profile_uplink.RULE_ID_SIZE
ack_index_w = ack_index_dtag + profile_uplink.T
ack_index_c = ack_index_w + profile_uplink.M
ack_index_bitmap = ack_index_c + 1
ack_index_padding = ack_index_bitmap + profile_uplink.BITMAP_SIZE

# Fragment the file.
fragmenter = Fragmenter(profile_uplink, message)
fragment_list = fragmenter.fragment()
last_window = len(fragment_list) // profile_uplink.WINDOW_SIZE

# The fragment sender MUST initialize the Attempts counter to 0 for that Rule ID and DTag value pair
# (a whole SCHC packet)
attempts = 0
fragment = None

if len(fragment_list) > (2 ** profile_uplink.M) * profile_uplink.WINDOW_SIZE:
    print(len(fragment_list))
    print((2 ** profile_uplink.M) * profile_uplink.WINDOW_SIZE)
    print("ERROR: The SCHC packet cannot be fragmented in 2 ** M * WINDOW_SIZE fragments or less. A Rule ID cannot be "
          "selected.")
    exit(1)

# Start sending fragments.
while i < len(fragment_list):

    # A fragment has the format "fragment = [header, payload]".
    data = bytes(fragment_list[i][0] + fragment_list[i][1])
    current_size += len(fragment_list[i][1])
    percent = round(float(current_size) / float(total_size) * 100, 2)

    # Convert to a Fragment class for easier manipulation.
    resent = None
    timeout = False
    fragment = Fragment(profile_uplink, fragment_list[i])

    # Send the data.
    print("Sending...")

    # On All-0 fragments, this function will wait for SIGFOX_DL_TIMER to expire
    # On All-1 fragments, this function will enter retransmission phase.
    post(fragment)
