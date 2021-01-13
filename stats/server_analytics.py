import pandas as pd
import json

pd.set_option('display.max_columns', None)

# json_file = json.loads('/Users/sergioaguilar/PycharmProjects/SCHCfox/stats/files/stats_file_v2.json')
with open('files/server/fragments_stats_v4.0.json') as json_file:
    data = json.load(json_file)

df1 = pd.read_json(str(json.dumps(data, sort_keys=True)))
print(df1)
df1_transposed = df1.T  # or df1.transpose()
print(df1_transposed)
df1_transposed.astype({"FCN": str, "RULE_ID": str,  "W": str,  "ack": str, "ack_send": str,
                       "data": str, "downlink_enable": bool, "fragment_size": int,
                       "lost": bool, "send_time": float, "sending_end": float,
                       "sending_start": float,
                       "seqNumber": int})
print(df1_transposed)
print(df1_transposed['FCN'].isin(['111']))
df_nowait = df1_transposed[df1_transposed['FCN'].isin(['111'])]
print(df_nowait)
df1_transposed['Branded'] = df1_transposed['FCN'].str.contains('111')*1
print(df1_transposed)
# df1_transposed.to_excel('test_stats_2.2.xlsx', engine='xlsxwriter')









