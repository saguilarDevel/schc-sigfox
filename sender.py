import json
import time

import requests
from requests import Timeout

from Entities.Fragmenter import Fragmenter
from Entities.Sigfox import Sigfox
from Messages.Fragment import Fragment

filename = "example.txt"
seqNumber = 1
device = "4D5A87"


def post(data_sent, profile, ack_expected):
    global seqNumber, attempts
    if ack_expected:
        attempts += 1
    url = "http://0.0.0.0:5000/post/wyschc-get"
    headers = {'content-type': 'application/json'}
    http_timeout = profile.RETRANSMISSION_TIMER_VALUE if ack_expected else 45
    payload_dict = {
        "deviceType": "WYSCHC",
        "device": device,
        "time": str(int(time.time())),
        "data": data_sent,
        "seqNumber": str(seqNumber),
        "ack": ack_expected
    }

    print(f"[POST] Posting fragment to {url}")

    try:
        response = requests.post(url, data=json.dumps(payload_dict), headers=headers, timeout=http_timeout)
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
        if ack_expected:
            # If the attempts counter is strictly less than MAX_ACK_REQUESTS, try again
            if attempts < profile_uplink.MAX_ACK_REQUESTS:
                print("SCHC Timeout reached while waiting for an ACK. Sending the ACK Request again...")
                return post(data_sent, profile, ack_expected)
            # Else, exit with an error.
            else:
                print("ERROR: MAX_ACK_REQUESTS reached. Goodbye!")
                print("A Sender-Abort must be sent...")
                exit(1)

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
index_bitmap = profile_uplink.RULE_ID_SIZE + profile_uplink.T + profile_uplink.M
index_c = index_bitmap + profile_uplink.BITMAP_SIZE

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
    print(
        "The SCHC packet cannot be fragmented in 2 ** M * WINDOW_SIZE fragments or less. A Rule ID cannot be selected.")

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
    http_message, ack = post(data, profile_uplink, ack_expected=fragment.expects_ack())

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
        ack_decoded = ack.decode()
        ack_window = int(ack_decoded[profile_uplink.RULE_ID_SIZE + profile_uplink.T:index_bitmap], 2)
        bitmap = ack_decoded[index_bitmap:index_bitmap + profile_uplink.BITMAP_SIZE]
        c = ack_decoded[index_c]
        print(f"ACK: {ack_decoded}")
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
                        f"The {str(j)}th ({str((2 ** profile_uplink.N - 1) * ack_window + j)} / {str(len(fragment_list))}) fragment was lost! Sending again...")
                    # Try sending again the lost fragment.
                    try:
                        fragment_to_be_resent = fragment_list[(2 ** profile_uplink.N - 1) * ack_window + j]
                        data_to_be_resent = bytes(fragment_to_be_resent[0] + fragment_to_be_resent[1])
                        print(f"Lost fragment: {data_to_be_resent}")
                        resent = post(data_to_be_resent, profile_uplink, ack_expected=False)
                    # If the fragment could not be indexed, we are at the last window with no fragment to be resent.
                    # The last fragment received should be an All-1.
                    except IndexError:
                        print("No fragment found.")
                        # Request las ACK sending the All-1 again.
                        _, last_ack = post(data, profile_uplink, ack_expected=True)

            # After retransmission (or not), proceed to the next window.
            current_window += 1
            i += 1
            continue

        # After sending the lost fragments, send the last ACK-REQ (All-0) again.
        if resent is not None:
            _, ack = post(data, profile_uplink, ack_expected=True)

        # After sending the lost fragments, if the last received fragment was an All-1,
        # we need to expect the last ACK.
        if fragment.is_all_1():
            # Get the last ACK.
            c = last_ack.decode()[index_c]

            if c == '1':
                if ack_window == (current_window % 2 ** profile_uplink.M):
                    print(
                        "Last ACK received: Fragments reassembled successfully. End of transmission. (While retransmitting)")
                    exit(0)
                else:
                    print("Last ACK window does not correspond to last window. (While retransmitting)")
                    exit(1)
