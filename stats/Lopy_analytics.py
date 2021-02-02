import pandas as pd
import json

pd.set_option('display.max_columns', None)

# json_file = json.loads('/Users/sergioaguilar/PycharmProjects/SCHCfox/stats/files/stats_file_v2.json')
with open('LoPy/stats_file_v2.7.json', encoding='ISO-8859-1') as json_file:
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
df1_transposed.astype({"downlink_enable": bool, "sending_start": float, "ack_received": bool, "data": str, "sending_end": float,
      "FCN": str, "fragment_size": int, "ack": str, "timeout": int, "RULE_ID": str, "rssi": int, "W": str, "send_time": float})
# print(df1_transposed.dtypes)
# print(df1_transposed.columns)
# print(df1_transposed[df1_transposed['download_enable'].isin([False])])


df_nowait = df1_transposed[df1_transposed['downlink_enable'].isin([False])]
print("Regular Fragments")
print(df_nowait['send_time'])
print("count:{}".format(df_nowait['send_time'].count()))
print("sum:{}".format(df_nowait['send_time'].sum(axis=0, skipna=True)))
print("mean:{}".format(df_nowait['send_time'].mean(axis=0, skipna=True)))
print("std:{}".format(df_nowait['send_time'].std(axis=0, skipna=True)))

df_wait = df1_transposed[df1_transposed['downlink_enable'].isin([True])]
print("Regular Fragments")
print(df_nowait['send_time'])
print("count:{}".format(df_nowait['send_time'].count()))
print("sum:{}".format(df_nowait['send_time'].sum(axis=0, skipna=True)))
print("mean:{}".format(df_nowait['send_time'].mean(axis=0, skipna=True)))
print("std:{}".format(df_nowait['send_time'].std(axis=0, skipna=True)))


if len(df_wait[df_wait['RULE_ID'] == "00"]) != 0:
    df_all0 = df_wait[df_wait['FCN'].isin(['000'])]
    df_all1 = df_wait[df_wait['FCN'].isin(['111'])]
else:
    df_all0 = df_wait[df_wait['FCN'].isin(['00000'])]
    df_all1 = df_wait[df_wait['FCN'].isin(['11111'])]


print("Fragments - downlink requested - ALL 0")
print(df_all0['send_time'])
print("count:{}".format(df_all0['send_time'].count()))
print("sum:{}".format(df_all0['send_time'].sum(axis=0, skipna=True)))
print("mean:{}".format(df_all0['send_time'].mean(axis=0, skipna=True)))
print("std:{}".format(df_all0['send_time'].std(axis=0, skipna=True)))


print("Fragments - downlink requested - ALL 1")
print(df_all1['send_time'])
print("count:{}".format(df_all1['send_time'].count()))
print("sum:{}".format(df_all1['send_time'].sum(axis=0, skipna=True)))
print("mean:{}".format(df_all1['send_time'].mean(axis=0, skipna=True)))
print("std:{}".format(df_all1['send_time'].std(axis=0, skipna=True)))

df1_transposed.to_excel('test_stats_2.2.xlsx', engine='xlsxwriter')

print("Transmission Time (excluding code overhead):{}".format(df1_transposed['send_time'].sum(axis=0, skipna=True)))
# print(df1['FCN'])



