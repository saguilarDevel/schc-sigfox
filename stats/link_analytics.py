import pandas as pd
import json

# Uncomment for complete diplay
pd.set_option('display.max_columns', None)
version = '5.8'
# json_file = json.loads('/Users/sergioaguilar/PycharmProjects/SCHCfox/stats/files/stats_file_v2.json')
# with open('files/LoPy/stats_file_v'+version+'.json') as json_file:
with open('files/LoPy/LoPy_stats_file_v'+version+'.json') as json_file:
    data = json.load(json_file)

df1 = pd.read_json(str(json.dumps(data, sort_keys=True)))
df1_transposed = df1.T # or df1.transpose()
print("Sum of fragments transmission duration: {}".format(df1_transposed['send_time'].sum(axis=0,skipna=True)))
df1_transposed.astype({"ack": str, "ack_received": bool, "data": str, "downlink_enable": bool, "fragment_size": int,
                       "rssi": int, "send_time": float, "sending_end": float, "sending_start": float, "timeout": int})
print(df1_transposed)
print('LoPy fragments')
# print(df1_transposed)
number_of_frames_sent = len(df1.columns)
print("number_of_frames_sent: {}".format(number_of_frames_sent))
# print(df1_transposed['ack_received'].value_counts())
received_acks = df1_transposed['ack_received'].values.sum()
print(df1_transposed['ack_received'].values.sum())
print(len(df1_transposed["ack_received"]) - sum(df1_transposed["ack_received"]))
lost_acks = len(df1_transposed["ack_received"]) - sum(df1_transposed["ack_received"])

ack_loss_rate = lost_acks / (len(df1_transposed["ack_received"]))
print("ack loss rate: {}".format(ack_loss_rate))

print("count:{}".format(df1_transposed['rssi'].count()))
print("sum:{}".format(df1_transposed['rssi'].sum(axis=0, skipna=True)))
print("mean:{}".format(df1_transposed['rssi'].mean(axis=0, skipna=True)))
print("std:{}".format(df1_transposed['rssi'].std(axis=0, skipna=True)))


with open('files/server/fragments_stats_v'+version+'.json') as json_file:
    data = json.load(json_file)

df2 = pd.read_json(str(json.dumps(data, sort_keys=True)))
# print(df2)
df2_transposed = df2.T  # or df1.transpose()
# print(df2_transposed)
df2_transposed.astype({"s-ack": str, "s-ack_send": str,
                       "s-data": str, "s-downlink_enable": bool, "s-fragment_size": int,
                       "s-send_time": float, "s-sending_end": float,
                       "s-sending_start": float,
                       "seqNumber": int})
print("server fragments")
print(df2_transposed)
number_of_received_frames = len(df2.columns)
print("number_of_received_frames: {}".format(number_of_received_frames))
frame_loss_rate = (number_of_frames_sent - number_of_received_frames) / number_of_frames_sent
if frame_loss_rate != 0:
    print("ack lost rate must be corrected")
    new_ack_lost_rate = received_acks / (number_of_received_frames)
else:
    new_ack_lost_rate = ack_loss_rate

print("summary:")
print("number_of_frames_sent: {}".format(number_of_frames_sent))
print("number_of_received_frames: {}".format(number_of_received_frames))
print("received_acks:{}".format(received_acks))
print("ack loss rate: {}".format(new_ack_lost_rate))
print("frame loss rate: {}".format(frame_loss_rate))

