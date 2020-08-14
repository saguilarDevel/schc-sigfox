# -*- coding: utf-8 -*-

from math import ceil, floor
from Messages.Header import Header

def zfill(string, width):
    if len(string) < width:
        return ("0" * (width - len(string))) + string
    else:
        return string

class Fragmenter:
	profile = None
	schc_packet = None

	def __init__(self, profile, schc_packet):
		self.profile = profile
		self.schc_packet = schc_packet

	def fragment(self):
		payload_max_length = int((self.profile.MTU - self.profile.HEADER_LENGTH) / 8)
		message = self.schc_packet
		fragment_list = []
		n = self.profile.N
		m = self.profile.M
		number_of_fragments = int(ceil(float(len(message)) / payload_max_length))

		print("[FRGM] Fragmenting message into " + str(number_of_fragments) + " pieces...")

		for i in range(number_of_fragments):
			w = zfill(bin(int(floor((i/(2**n - 1) % (2 ** m)))))[2:], 2)
			fcn = zfill(bin((2 ** n - 2) - (i % (2 ** n - 1)))[2:], 3)

			fragment_payload = message[i * payload_max_length:(i + 1) * payload_max_length]

			if len(fragment_payload) < payload_max_length:
				header = Header(self.profile, rule_id="00", dtag="0", w=w, fcn="111", c=0)

			else:
				header = Header(self.profile, rule_id="00", dtag="0", w=w, fcn=fcn, c=0)

			fragment = [header.bytes, fragment_payload]
			# print("[" + header.string + "]" + str(fragment_payload))
			fragment_list.append(fragment)

		print("[FRGM] Fragmentation complete.")

		return fragment_list
