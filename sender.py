import requests
import time

from Entities.Fragmenter import Fragmenter
from Entities.Sigfox import Sigfox
from Messages.Fragment import Fragment

filename = "example.txt"
seqNumber = 1


def post(data):
	global seqNumber
	payload = {
		"deviceType": "WYSCHC",
		"device": "4D5A87",
		"time": str(int(time.time())),
		"data": data,
		"seqNumber": str(seqNumber)
	}
	seqNumber += 1
	url = "http://0.0.0.0:5000/post/message"
	return requests.post(url, json=payload)


# Read the file to be sent.
with open(filename, "rb") as data:
	f = data.read()
	payload = bytearray(f)

# Initialize variables.
total_size = len(payload)
current_size = 0
percent = round(0, 2)
ack = None
last_ack = None
i = 0
current_window = 0
profile_uplink = Sigfox("UPLINK", "ACK ON ERROR")
profile_downlink = Sigfox("DOWNLINK", "NO ACK")

# Fragment the file.
fragmenter = Fragmenter(profile_uplink, payload)
fragment_list = fragmenter.fragment()

# The fragment sender MUST initialize the Attempts counter to 0 for that Rule ID and DTag value pair
# (a whole SCHC packet)
attempts = 0
retransmitting = False
fragment = None

if len(fragment_list) > (2 ** profile_uplink.M) * profile_uplink.WINDOW_SIZE:
	print(len(fragment_list))
	print((2 ** profile_uplink.M) * profile_uplink.WINDOW_SIZE)
	print("The SCHC packet cannot be fragmented in 2 ** M * WINDOW_SIZE fragments or less. A Rule ID cannot be selected.")
	# What does this mean?

# Start sending fragments.
while i < len(fragment_list):

	if not retransmitting:
		# A fragment has the format "fragment = [header, payload]".
		data = bytes(fragment_list[i][0] + fragment_list[i][1])
		current_size += len(fragment_list[i][1])
		percent = round(float(current_size) / float(total_size) * 100, 2)

		# Send the data.
		print("Sending...")
		post(data)
		print(str(current_size) + " / " + str(total_size) + ", " + str(percent) + "%")

		# Convert to a Fragment class for easier manipulation.
		fragment = Fragment(profile_uplink, fragment_list[i])

	# If a fragment is an All-0 or an All-1:
	if retransmitting or fragment.is_all_0() or fragment.is_all_1():

		# Juan Carlos dijo que al enviar un ACKREQ el contador se reinicia.
		attempts = 0

		# Set the timeout for RETRANSMISSION_TIMER_VALUE.
		the_socket.settimeout(profile_uplink.RETRANSMISSION_TIMER_VALUE)

		while attempts < profile_uplink.MAX_ACK_REQUESTS:

			# Try receiving an ACK from the receiver.
			try:
			ack, address = the_socket.recvfrom(profile_downlink.MTU)
				print("ACK received.")
				index = profile_uplink.RULE_ID_SIZE + profile_uplink.T + profile_uplink.M
				bitmap = ack.decode()[index:index + profile_uplink.BITMAP_SIZE]
				ack_window = int(ack.decode()[profile_uplink.RULE_ID_SIZE + profile_uplink.T:index], 2)
				print("ACK_WINDOW " + str(ack_window))
				print(ack.decode())
				print(bitmap)

				index_c = index + profile_uplink.BITMAP_SIZE
				c = ack.decode()[index_c]

				print(c)

				# If the C bit of the ACK is set to 1 and the fragment is an All-1 then we're done.
				if c == '1' and fragment.is_all_1():
					if ack_window == current_window:
						print("Last ACK received: Fragments reassembled successfully. End of transmission.")
						break
					else:
						print("Last ACK window does not correspond to last window")
						exit(1)

				# If the C bit is set to 1 and the fragment is an All-0 then something naughty happened.
				elif c == '1' and fragment.is_all_0():
					print("You shouldn't be here. (All-0 with C = 1)")
					exit(1)

				# If the C bit has not been set:
				elif c == '0':

					resent = False
					# Check the bitmap.
					for j in range(len(bitmap)):
						# If the j-th bit of the bitmap is 0, then the j-th fragment was lost.
						if bitmap[j] == '0':

							print("The " + str(j) + "th (" + str(
								(2 ** profile_uplink.N - 1) * ack_window + j) + " / " + str(
								len(fragment_list)) + ") fragment was lost! Sending again...")

							# Try sending again the lost fragment.
							try:
								fragment_to_be_resent = fragment_list[(2 ** profile_uplink.N - 1) * ack_window + j]
								data_to_be_resent = bytes(fragment_to_be_resent[0] + fragment_to_be_resent[1])
								print(data_to_be_resent)
								post(data_to_be_resent)
								resent = True

							# If the fragment wasn't found, it means we're at the last window with no fragment
							# to be resent. The last fragment received is an All-1.
							except IndexError:
								print("No fragment found.")
								resent = False
								retransmitting = False

								# Request last ACK sending the All-1 again.
								post(data)

					# After sending the lost fragments, send the last ACK-REQ again
					if resent:
						post(data)
						retransmitting = True
						break

					# After sending the lost fragments, if the last received fragment was an All-1 we need to receive
					# the last ACK.
					if fragment.is_all_1():

						# Set the timeout for RETRANSMISSION_TIMER_VALUE
						the_socket.settimeout(profile_uplink.RETRANSMISSION_TIMER_VALUE)

						# Try receiving the last ACK.
						try:
							last_ack, address = the_socket.recvfrom(profile_downlink.MTU)
							c = last_ack.decode()[index_c]

							# If the C bit is set to 1 then we're done.
							if c == '1':
								print(ack_window)
								print(current_window)
								if ack_window == (current_window % 2**profile_uplink.M):
									print("Last ACK received: Fragments reassembled successfully. End of transmission. (While retransmitting)")
									break
								else:
									print("Last ACK window does not correspond to last window. (While retransmitting)")
									exit(1)

						# If the last ACK was not received, raise an error.
						except socket.timeout:
							attempts += 1
							if attempts < profile_uplink.MAX_ACK_REQUESTS:

								# TODO: What happens when the ACK gets lost?

								print("No ACK received (RETRANSMISSION_TIMER_VALUE). Waiting for it again...")
							else:
								print("MAX_ACK_REQUESTS reached. Goodbye.")
								print("A sender-abort MUST be sent...")
								exit(1)

				# Proceed to next window.
				print("Proceeding to next window")
				resent = False
				retransmitting = False
				current_window += 1
				break

			# If no ACK was received
			except socket.timeout:
				attempts += 1
				if attempts < profile_uplink.MAX_ACK_REQUESTS:

					# TODO: What happens when the ACK gets lost?

					print("No ACK received (RETRANSMISSION_TIMER_VALUE). Waiting for it again...")
				else:
					print("MAX_ACK_REQUESTS reached. Goodbye.")
					print("A sender-abort MUST be sent...")
					exit(1)
		else:
			print("MAX_ACK_REQUESTS reached. Goodbye.")
			print("A sender-abort MUST be sent...")
			exit(1)

	# Continue to next fragment
	if not retransmitting:
		i += 1