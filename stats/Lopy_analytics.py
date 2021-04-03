import os

import pandas as pd
import json


def extract_data(filename, output):
    pd.set_option('display.max_columns', None)

    output.write(f"-------------- RESULTS FOR {filename} --------------\n\n")

    with open(filename, encoding='ISO-8859-1') as json_file:
        data = json.load(json_file)

    tx_json = {'fragmentation_time': data['fragmentation_time'],
               'payload_size': data['payload_size'],
               'total_number_of_fragments': data['total_number_of_fragments'],
               'total_transmission_time': data['total_transmission_time']}
    output.write(f"tx_json = {tx_json}\n\n")
    df_tx = pd.DataFrame(tx_json, index=[0])
    df_tx = df_tx.T
    output.write(f"dl_tx = {df_tx}\n\n")

    assert data['fragments']
    df1 = pd.read_json(str(json.dumps(data['fragments'], sort_keys=True)))
    # print(df1)
    # df1.astype({"Column 1": int, "Column 2": int, "Column 3": int})
    # df1.astype({"Column 6": bool})
    # print(df1.dtypes)
    df1_transposed = df1.T  # or df1.transpose()
    output.write(f"df1_transposed = {df1_transposed} \n\n")
    df1_transposed.astype(
        {"downlink_enable": bool, "sending_start": float, "ack_received": bool, "data": str, "sending_end": float,
         "FCN": str, "fragment_size": int, "ack": str, "timeout": int, "RULE_ID": str, "rssi": int, "W": str,
         "send_time": float})
    # print(df1_transposed.dtypes)
    # print(df1_transposed.columns)
    # print(df1_transposed[df1_transposed['download_enable'].isin([False])])

    df_nowait = df1_transposed[df1_transposed['downlink_enable'].isin([False])]

    output.write(f"Regular Fragments (nowait)\n"
                 f"send_time = {df_nowait['send_time']}"
                 f"count: {df_nowait['send_time'].count()}\n"
                 f"sum: {df_nowait['send_time'].sum(axis=0, skipna=True)}\n"
                 f"mean: {df_nowait['send_time'].mean(axis=0, skipna=True)}\n"
                 f"std: {df_nowait['send_time'].std(axis=0, skipna=True)}\n"
                 f"\n")

    df_wait = df1_transposed[df1_transposed['downlink_enable'].isin([True])]

    output.write(f"Regular Fragments (wait)\n"
                 f"send_time = {df_wait['send_time']}"
                 f"count: {df_wait['send_time'].count()}\n"
                 f"sum: {df_wait['send_time'].sum(axis=0, skipna=True)}\n"
                 f"mean: {df_wait['send_time'].mean(axis=0, skipna=True)}\n"
                 f"std: {df_wait['send_time'].std(axis=0, skipna=True)}\n"
                 f"\n")

    if len(df_wait[df_wait['RULE_ID'] == "00"]) != 0:
        df_all0 = df_wait[df_wait['FCN'].isin(['000'])]
        df_all1 = df_wait[df_wait['FCN'].isin(['111'])]
    else:
        df_all0 = df_wait[df_wait['FCN'].isin(['00000'])]
        df_all1 = df_wait[df_wait['FCN'].isin(['11111'])]

    output.write(f"Fragments - downlink requested - ALL 0\n"
                 f"send_time = {df_all0['send_time']}"
                 f"count: {df_all0['send_time'].count()}\n"
                 f"sum: {df_all0['send_time'].sum(axis=0, skipna=True)}\n"
                 f"mean: {df_all0['send_time'].mean(axis=0, skipna=True)}\n"
                 f"std: {df_all0['send_time'].std(axis=0, skipna=True)}\n"
                 f"\n")

    output.write(f"Fragments - downlink requested - ALL 1\n"
                 f"send_time = {df_all1['send_time']}"
                 f"count: {df_all1['send_time'].count()}\n"
                 f"sum: {df_all1['send_time'].sum(axis=0, skipna=True)}\n"
                 f"mean: {df_all1['send_time'].mean(axis=0, skipna=True)}\n"
                 f"std: {df_all1['send_time'].std(axis=0, skipna=True)}\n"
                 f"\n")

    df1_transposed.to_excel('test_stats_2.2.xlsx', engine='xlsxwriter')
    output.write(f"Transmission Time (excluding code overhead):{df1_transposed['send_time'].sum(axis=0, skipna=True)}\n\n")


if __name__ == '__main__':
    folders = ["10_ul", "20_ul", "10_uldl", "20_uldl"]
    os.chdir("stats")
    with open("output.txt", 'w') as output_file:
        for foldername in folders:
            print(f"Current folder: {foldername}")
            output_file.write(f"============== FOLDER: {foldername} ==============\n\n")
            for file in os.listdir(f'results/{foldername}'):
                print(f"Extracting data from {foldername}/{file}")
                extract_data(f"results/{foldername}/{file}", output_file)
