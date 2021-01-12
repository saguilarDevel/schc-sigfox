import pandas as pd
import json
import requests

# Uncomment for complete diplay
# pd.set_option('display.max_columns', None)
version = '2.7'
# json_file = json.loads('/Users/sergioaguilar/PycharmProjects/SCHCfox/stats/files/stats_file_v2.json')
with open('files/LoPy/stats_file_v'+version+'.json') as json_file:
    data = json.load(json_file)

tx_json = {}
tx_json['fragmentation_time'] = data['fragmentation_time']
tx_json['payload_size'] = data['payload_size']
tx_json['total_number_of_fragments'] = data['total_number_of_fragments']
tx_json['total_transmission_time'] = data['total_transmission_time']
# print(tx_json)
df_tx = pd.DataFrame(tx_json, index=[0])
df_tx = df_tx.T
# print(df_tx)

assert data['fragments']
df1 = pd.read_json(str(json.dumps(data['fragments'], sort_keys=True)))
# print(df1)
# df1.astype({"Column 1": int, "Column 2": int, "Column 3": int})
# df1.astype({"Column 6": bool})
# print(df1.dtypes)
df1_transposed = df1.T # or df1.transpose()
print("Sum of fragments transmission duration: {}".format(df1_transposed['send_time'].sum(axis=0,skipna=True)))
print(df1_transposed)
df1_transposed.astype({"FCN": str, "RULE_ID": str,  "W": str,  "ack": str, "data": str, "download_enable": bool,
                       "rssi": int, "send_time": float, "sending_end": float, "sending_start": float})
print('LoPy fragments')
print(df1_transposed)
# print(df1_transposed.dtypes)
# print(df1_transposed.columns)
# print(df1_transposed[df1_transposed['download_enable'].isin([False])])

df_nowait = df1_transposed[df1_transposed['download_enable'].isin([False])]
print("\nRegular Fragments")
print(df_nowait['send_time'])
print("sum:{}".format(df_nowait['send_time'].sum(axis=0, skipna=True)))
print("std:{}".format(df_nowait['send_time'].std(axis=0, skipna=True)))
print("mean:{}".format(df_nowait['send_time'].mean(axis=0, skipna=True)))

df_wait = df1_transposed[df1_transposed['download_enable'].isin([True])]
print("\nFragments - download requested")
print(df_wait['send_time'])
print("sum:{}".format(df_wait['send_time'].sum(axis=0, skipna=True)))
print("std:{}".format(df_wait['send_time'].std(axis=0, skipna=True)))
print("mean:{}".format(df_wait['send_time'].mean(axis=0, skipna=True)))

df_all_0 = df_wait[df_wait['FCN'].isin(['000'])]
print("\nAll-0 Fragments")
print(df_all_0['send_time'])
print("sum:{}".format(df_all_0['send_time'].sum(axis=0, skipna=True)))
print("std:{}".format(df_all_0['send_time'].std(axis=0, skipna=True)))
print("mean:{}".format(df_all_0['send_time'].mean(axis=0, skipna=True)))

df_all_0 = df_wait[df_wait['FCN'].isin(['111'])]
print("\nAll-1 Fragments")
print(df_all_0['send_time'])
#print("sum:{}".format(df_wait['send_time'].sum(axis=0, skipna=True)))
#print("std:{}".format(df_wait['send_time'].std(axis=0, skipna=True)))
#print("mean:{}".format(df_wait['send_time'].mean(axis=0, skipna=True)))

# df_nowait = df1_transposed[df1_transposed['downlink_enable'].isin([False])]
# print("Fragments - no donwlink requested")
# print(df_nowait['send_time'])
# print("std:{}".format(df_nowait['send_time'].std(axis=0, skipna=True)))
# print("mean:{}".format(df_nowait['send_time'].mean(axis=0, skipna=True)))
#
# df_wait = df1_transposed[df1_transposed['downlink_enable'].isin([True])]
# print("Fragments - downlink requested")
# print(df_wait['send_time'])
# print("std:{}".format(df_wait['send_time'].std(axis=0, skipna=True)))
# print("mean:{}".format(df_wait['send_time'].mean(axis=0, skipna=True)))

# df1_transposed.to_excel('test_stats_2.2.xlsx', engine='xlsxwriter')

# print(df1['FCN'])

with open('files/server/fragments_stats_v'+version+'.json') as json_file:
    data = json.load(json_file)

df2 = pd.read_json(str(json.dumps(data, sort_keys=True)))
# print(df2)
df2_transposed = df2.T  # or df1.transpose()
# print(df2_transposed)
df2_transposed.astype({"FCN": str, "RULE_ID": str,  "W": str,  "s-ack": str, "s-ack_send": str,
                       "s-data": str, "s-downlink_enable": bool, "s-fragment_size": int,
                       "s-lost": bool, "s-send_time": float, "s-sending_end": float,
                       "s-sending_start": float,
                       "seqNumber": int})
print("server fragments")
print(df2_transposed)
# print(df2_transposed['FCN'].isin(['111']))
# df2_nowait = df2_transposed[df1_transposed['FCN'].isin(['111'])]
# print(df_nowait)
# # df1_transposed['Branded'] = df1_transposed['FCN'].str.contains('111')*1
# print(df1_transposed)


# merged_inner = pd.merge(left=df1_transposed, right=df2_transposed, how='left',
#                         left_on=['FCN', 'RULE_ID', 'W'],
#                         right_on=['FCN', 'RULE_ID', 'W'])
#merged = pd.merge(df2_transposed, df1_transposed, on=["FCN", "RULE_ID", "W"])
concat = pd.concat([df2_transposed, df1_transposed], keys=["Cloud", "LoPy"])

print(concat)
#no_duplicates = merged.drop_duplicates(subset=['seqNumber',"send_time"])
#no_duplicates.sort_values(by=['seqNumber']).to_excel('no_dup_test_stats_v'+version+'_2.xlsx', engine='xlsxwriter')
concat.sort_values(by=['seqNumber']).to_excel('merged_test_stats_v'+version+'_2.xlsx', engine='xlsxwriter')
# concat = pd.concat([df1_transposed, df2_transposed]).drop_duplicates().reset_index(drop=True)
# print(concat)