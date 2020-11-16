import pandas as pd
import json

# json_file = json.loads('/Users/sergioaguilar/PycharmProjects/SCHCfox/stats/files/stats_file.json')
with open('files/stats_file.json') as json_file:
    data = json.load(json_file)

df1 = pd.read_json(str(json.dumps(data, sort_keys=True)))
df1_transposed = df1.T # or df1.transpose()
print(df1_transposed)
print(df1.dtypes)
# df1.astype({"Column 1": int, "Column 2": int, "Column 3": int})
# print(df1['FCN'])



