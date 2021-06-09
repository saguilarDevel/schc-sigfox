import binascii

import requests

from Entities.SCHCSender import SCHCSender

from config import config

print("This is the SENDER script for a SCHC transmission experiment")
input("Press enter to continue....")

with open("Packets/300", "rb") as data:
    f = data.read()
    payload = bytearray(f)

sender = SCHCSender()
# sender.set_logging(filename="logs.log", json_file=filename_stats)
sender.set_session("ACK ON ERROR", payload)
sender.set_device("4d5a87")

_ = requests.post(url=config.LOCAL_CLEAN_URL, json={'header_bytes': sender.HEADER_BYTES,
                                                    'not_delete_dl_losses': "False",
                                                    'clear': 'True'})

# sender.TIMER.wait(10, raise_exception=False)

sender.start_session()

input("Press Enter to exit.")
