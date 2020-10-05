# This is the beacon module to be run for experiments...

from network import Sigfox
import socket
import time
import pycom

def zfill(string, width):
	if len(string) < width:
		return ("0" * (width - len(string))) + string
	else:
		return string


# init Sigfox for RCZ4 (Chile)
# sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ4)
# init Sigfox for RCZ1 (Europe)
sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ1)

s = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
s.setblocking(True)
# set False for only uplink, true for BIDIR
s.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, True)
s.settimeout(45)

c = 10
submerged_time = 0
n = 1

# Wait for the beacon to be submerged
time.sleep(submerged_time)

# Send n messages to the Sigfox network to test connectivity
for i in range(n):

	string = "{}{}".format(zfill(str(c), 3), zfill(str(i), 3))
	payload = bytes(string.encode())
	print("Sending...")
	# s.send(payload)
	print("Sent.")
	print(payload)
	# try:
	pycom.rgbled(0x6600CC)
	print("Sending: {}".format(payload))
	s.send(payload)
	response = s.recv(12 * 8)
	print("response -> {}".format(response))
	decode_response = ''.join("{:08b}".format(int(byte)) for byte in response)
	print('decode_response -> {}'.format(decode_response))
# time.sleep(wait_time)
# except OSError as e:
# 	print('Error number {}, {}'.format(e.args[0],e))
# 	if e.args[0] == 11:
# 		# Retry Logic
# 		print('Error {}, {}'.format(e.args[0],e))

time.sleep(30)

print("Done")
