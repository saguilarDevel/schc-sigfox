import pandas as pd
import json

pd.set_option('display.max_columns', None)

# json_file = json.loads('/Users/sergioaguilar/PycharmProjects/SCHCfox/stats/files/stats_file_v2.json')
with open('files/stats_file.json') as json_file:
    data = json.load(json_file)

tx_json = {}
tx_json['fragmentation_time'] = data['fragmentation_time']
tx_json['payload_size'] = data['payload_size']
tx_json['total_number_of_fragments'] = data['total_number_of_fragments']
tx_json['total_transmission_time'] = data['total_transmission_time']
print(tx_json)
df_tx = pd.DataFrame(tx_json, index=[0])
df_tx = df_tx.T
print(df_tx)

assert data['fragments']
df1 = pd.read_json(str(json.dumps(data['fragments'], sort_keys=True)))
# print(df1)
# df1.astype({"Column 1": int, "Column 2": int, "Column 3": int})
# df1.astype({"Column 6": bool})
# print(df1.dtypes)
df1_transposed = df1.T # or df1.transpose()
print(df1_transposed)
df1_transposed.astype({"FCN": str, "RULE_ID": str,  "W": str,  "ack": str, "data": str, "download_enable": bool,
                       "rssi": int, "send_time": float, "sending_end": float, "sending_start": float})
# print(df1_transposed.dtypes)
# print(df1_transposed.columns)
# print(df1_transposed[df1_transposed['download_enable'].isin([False])])


df_nowait = df1_transposed[df1_transposed['downlink_enable'].isin([False])]
print("Fragments - no donwlink requested")
print(df_nowait['send_time'])
print("std:{}".format(df_nowait['send_time'].std(axis=0, skipna=True)))
print("mean:{}".format(df_nowait['send_time'].mean(axis=0, skipna=True)))

df_wait = df1_transposed[df1_transposed['downlink_enable'].isin([True])]
print("Fragments - downlink requested")
print(df_wait['send_time'])
print("std:{}".format(df_wait['send_time'].std(axis=0, skipna=True)))
print("mean:{}".format(df_wait['send_time'].mean(axis=0, skipna=True)))

df1_transposed.to_excel('test_stats.xlsx', engine='xlsxwriter')

# print(df1['FCN'])



