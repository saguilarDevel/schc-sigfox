import requests
import json


def send_request(sendData, timeout):
    url = 'http://localhost:5000/post/message'
    headers = {'content-type': 'application/json'}
    print('sendData -> {}'.format(sendData))
    data_dict = {
        "deviceType": "01B29CC4",
        "device": "1B29CC4",
        "time": "1596713121",
        "data": "".format(sendData),
        "seqNumber": "39",
        "ack": "false"
    }
    response = requests.post(url, data=json.dumps(data_dict), headers=headers, timeout=timeout)
    print('response -> {}'.format(response))
    return response


msg1 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1599043008', 'data': '063132333435363738393130',
        'seqNumber': '49', 'ack': 'false'}
msg2 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1599043019', 'data': '053131313231333134313531',
        'seqNumber': '50', 'ack': 'false'}
msg3 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1599043030', 'data': '043631373138313932303231',
        'seqNumber': '51', 'ack': 'false'}
msg4 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1599043040', 'data': '033232323332343235323632',
        'seqNumber': '52', 'ack': 'false'}
msg5 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1599043047', 'data': '023732383239333033313332',
        'seqNumber': '53', 'ack': 'false'}
msg6 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1599043056', 'data': '013333333433353336333733',
        'seqNumber': '54', 'ack': 'false'}
msg7 = {'deviceType': '01B29CC4', 'device': '1B29CC4', 'time': '1599043069', 'data': '003833393430343134323433',
        'seqNumber': '55', 'ack': 'false'}

msgs = [msg1, msg2, msg3, msg4, msg5, msg6, msg7]

for i, msg in enumerate(msgs):
    print('sending msg {}, {}'.format(i, msg))
    response = send_request(msg, 45)
    print('response -> '.format(response))
