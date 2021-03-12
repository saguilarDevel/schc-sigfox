import requests
import json
import time

from config import config


def send_request(sendData, timeout):
    url = 'http://localhost:5000/wyschc_get'
    url_ngrok = 'https://d347a0efcb92.ngrok.io/wyschc_get'
    url_cloud = config.RECEIVER_URL
    headers = {'content-type': 'application/json'}
    print('sendData -> {}'.format(sendData))
    response = requests.post(url_cloud,
                             data=json.dumps(sendData),
                             headers=headers,
                             timeout=timeout)
    # print('response -> {}'.format(response))
    return response


msg1 = {
  "deviceType": "01B29CC4",
  "device": "1B29CC4",
  "time": "1599043008",
  "data": "063132333435363738393130",
  "seqNumber": "49",
  "ack": "false"
}
msg2 = {"deviceType": "01B29CC4", "device": "1B29CC4", "time": "1599043019", "data": "053131313231333134313531",
        "seqNumber": "50", "ack": "false"}
msg3 = {"deviceType": "01B29CC4", "device": "1B29CC4", "time": "1599043030", "data": "073132333435",
        "seqNumber": "51", "ack": "true"}


msg2_1 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1602249495', 'data': '063132333435363738393132',
          'seqNumber': '391', 'ack': 'false'}
msg2_2 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1602249504', 'data': '053334353637383931323334',
          'seqNumber': '392', 'ack': 'false'}
msg2_3 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1602249513', 'data': '043536373839313233343536',
          'seqNumber': '393', 'ack': 'false'}
msg2_4 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1602249523', 'data': '033738393132333435363738',
          'seqNumber': '394', 'ack': 'false'}
msg2_5 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1602249533', 'data': '023931323334353637383931',
          'seqNumber': '395', 'ack': 'false'}
msg2_6 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1602249545', 'data': '013233343536373839313233',
          'seqNumber': '396', 'ack': 'false'}
msg2_7 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1602249554', 'data': '003435363738393132333435',
          'seqNumber': '397', 'ack': 'true'}
msg2_8 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1602249599', 'data': '0e3637383931323334353637',
          'seqNumber': '398', 'ack': 'false'}
msg2_9 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1602249609', 'data': '0f3839',
          'seqNumber': '399', 'ack': 'true'}

msgs1 = [msg1, msg2, msg3]
msgs2 = [msg2_1, msg2_2, msg2_3, msg2_4, msg2_5, msg2_6, msg2_7, msg2_8, msg2_9]

for i, msg in enumerate(msgs2):
    print('sending msg {}, {}'.format(i, msg))
    response = send_request(msg, 45)
    if response.status_code == 204:
        print('No content in response')
    elif response.status_code == 500:
        print('Error in server')
        break
    elif response.status_code == 200:
        print('response -> {}'.format(response.text))

    time.sleep(5)

print("Finish")


# 07f7ffffffffffff
# 0000011111110111111111111111111111111111111111111111111111111111
# 080fffffffffffff
# 0000100000001111111111111111111111111111111111111111111111111111
# 0af8000000000000
# 0000101011111000000000000000000000000000000000000000000000000000