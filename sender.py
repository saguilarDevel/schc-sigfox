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


def post(fragment_sent):
    global seqNumber, attempts, current_window
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
        seqNumber += 1
        print(f"[POST] Response: {response}")
        downlink_data = None
        http_code = response.status_code

        # If 500, exit with an error
        if http_code == 500:
            print("Response: 500 Internal Server Error")
            exit(1)

        # If 204, the fragment was posted successfully
        elif http_code == 204:
            print("Response: 204 No Content")

        # If 200, the fragment was posted and an ACK has been received.
        elif http_code == 200:
            print(f"Response: 200 OK, Text: {response.text}. Ressetting attempts counter to 0.")
            attempts = 0
            downlink_data = response.json()[device]["downlinkData"]

        return http_code, downlink_data

    # If the timer expires
    except Timeout:

        # If an ACK was expected
        if fragment_sent.is_all_1():
            # If the attempts counter is strictly less than MAX_ACK_REQUESTS, try again
            if attempts < profile_uplink.MAX_ACK_REQUESTS:
                print("SCHC Timeout reached while waiting for an ACK. Sending the ACK Request again...")
                return post(fragment_sent)
            # Else, exit with an error.
            else:
                print("ERROR: MAX_ACK_REQUESTS reached. Sending Sender-Abort.")
                header = fragment_sent.header
                abort = SenderAbort(profile, header)

                post(abort)

                print("A Sender-Abort must be sent...")
                exit(1)

        # If the ACK can be not sent
        if fragment_sent.is_all_0():
            print("All-0 timeout reached. Proceeding to next window.")
            current_window += 1
            return 204, None

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
ack = None
last_ack = None
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
    http_message, ack = post(fragment)

    # If 204, the fragment was sent successfully. Increase the fragment index
    if http_message == 204:
        i += 1
        continue

    # If 200, an ACK was received
    elif http_message == 200:
        if not fragment.expects_ack():
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

        # If the C bit is set to 1 and the fragment is an All-1, the transmission is complete
        if c == '1' and fragment.is_all_1():
            if ack_window == current_window:
                print("Last ACK received, fragments reassembled successfully. End of transmission.")
                exit(0)
            else:
                print("ERROR: Last ACK window does not correspond to last window.")
                exit(1)

        # If the C bit is set to 1 but the fragment is an All-0 then something naughty happened.
        elif c == '1' and fragment.is_all_0():
            print("ERROR: All-0 with C = 1")
            exit(1)

        # Else, if the C bit is 0, the transmission is not yet complete.
        elif c == '0':
            # Check the bitmap.
            for j in range(len(bitmap)):
                # If the j-th bit of the bitmap is 0, then the j-th fragment was lost.
                if bitmap[j] == '0':
                    print(
                        f"The "
                        f"{str(j)}th ({str((2 ** profile_uplink.N - 1) * ack_window + j)} / {str(len(fragment_list))}) "
                        f"fragment was lost! Sending again...")
                    # Try sending again the lost fragment.
                    try:
                        fragment_to_be_resent = Fragment(profile_uplink,
                                                         fragment_list[(2 ** profile_uplink.N - 1) * ack_window + j])
                        print(f"Lost fragment: {fragment_to_be_resent.string}")
                        resent = post(fragment_to_be_resent)
                    # If the fragment could not be indexed, we are at the last window with no fragment to be resent.
                    # The last fragment received should be an All-1.
                    except IndexError:
                        print("No fragment found.")
                        # Request las ACK sending the All-1 again.
                        _, last_ack = post(fragment)

            # After retransmission (or not), proceed to the next window.
            current_window += 1
            i += 1
            continue

        # After sending the lost fragments, send the last ACK-REQ (All-0) again.
        if resent is not None:
            _, ack = post(fragment)

        # After sending the lost fragments, if the last received fragment was an All-1,
        # we need to expect the last ACK.
        if fragment.is_all_1():
            # Get the last ACK.
            c = last_ack.decode()[ack_index_c]

            if c == '1':
                if ack_window == (current_window % 2 ** profile_uplink.M):
                    print(
                        "Last ACK received: Fragments reassembled successfully. End of transmission. (While "
                        "retransmitting)")
                    exit(0)
                else:
                    print("Last ACK window does not correspond to last window. (While retransmitting)")
                    exit(1)
