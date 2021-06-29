import binascii
import filecmp
import json

import requests

from Entities.SCHCLogger import SCHCLogger
from Entities.SCHCSender import SCHCSender

from config import config

loss_rates = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
repetitions = 500
json_filename = "recvd/results_3.json"

print("This is the SENDER script for a SCHC transmission experiment")
print(f"Loss rates: {loss_rates}")
print(f"Repetitions: {repetitions} per loss rate")
print(f"Saving in {json_filename}")
input("Press enter to continue...")

with open(config.PAYLOAD, "rb") as data:
    f = data.read()
    payload = bytearray(f)

with open(json_filename, "w") as f:
    exp_dict = {}
    f.write(json.dumps(exp_dict))

for loss_rate in loss_rates:
# for loss_rate in [50]:
    with open(json_filename, "r+") as f:
        exp_dict = json.load(f)
        print(exp_dict)
        exp_dict[loss_rate] = {}
        print(exp_dict)
        f.seek(0)
        f.write(json.dumps(exp_dict))
        f.truncate()

    for repetition in range(repetitions):

        print(f"====== LOSS RATE {loss_rate} | REPETITION {repetition + 1} ======")

        with open(config.RECEIVED, 'w') as f:
            f.write("")

        sender = SCHCSender()
        # sender.set_loss_mask("loss_masks/loss_mask_2.json")
        sender.set_session("ACK ON ERROR", payload)

        sender.PROFILE.RETRANSMISSION_TIMER_VALUE = 5
        sender.PROFILE.SIGFOX_DL_TIMEOUT = 5

        sender.set_logging(None, None, severity=SCHCLogger.INFO)
        sender.set_device("4d5a87")

        sender.set_loss_rate(loss_rate)

        _ = requests.post(url=config.LOCAL_CLEAN_URL, json={'header_bytes': sender.HEADER_BYTES,
                                                            'not_delete_dl_losses': "False",
                                                            'clear': 'True'})

        sender.start_session()

        sender.TIMER.wait(1, raise_exception=False)

        with open(json_filename, "r+") as f:
            exp_dict = json.load(f)
            exp_dict[str(loss_rate)][str(repetition)] = {
                "receiver_abort": sender.LOGGER.RECEIVER_ABORTED,
                "sender_abort": sender.LOGGER.SENDER_ABORTED,
                "reassemble_success": filecmp.cmp(config.PAYLOAD, config.RECEIVED),
                "uplink": sender.SENT,
                "downlink": sender.RECEIVED
            }

            f.seek(0)
            f.write(json.dumps(exp_dict))
            f.truncate()

        del sender

input("Press Enter to exit.")
