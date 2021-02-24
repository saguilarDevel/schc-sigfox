# Experiment guide

## Paramenters

The tests were made for:
* 4 packet sizes: 77, 150, 231, 512 bytes.
* FER of 10% and 20% on UL-Only and UL-DL (4 different cases, same FER for both directions)
* 10 repetitions per case, except for 77B where 20 repetitions were made.

This adds up to a total of **3\*4\*10 + 1\*4\*20 = 200 tests**.

## Callback

The Sigfox backend callback has the following JSON format:
```json
{
    "deviceType" : "01b29fc5",
    "device" : "{device}",
    "time" : "{time}",
    "data" : "{data}",
    "seqNumber" : "{seqNumber}",
    "ack" : "{ack}",
    "loss_rate" : 10 or 20,
    "enable_losses" : true or false,
    "enable_dl_losses" : true or false
}
```

## Cleaning function

The LoPy4 code works in a way such that the Clean HTTP function is executed at the start of every experiment. The function is executed with the `header_bytes` parameter defined by the length of the packet.

## LoPy code

After running `main.py`, a file named `stats_file_v2.7_{}_{}.json` is created for every packet size and repetition number. These files are to be analyzed using the `Lopy_analytics.py` script.
The main idea is to run all the experiments and then batch analyze them.

## Spreadsheet

The important parameters that we want are:
* Total transmission time
* Amount, total transmission time, average transmission time and standard deviation of transmission time for each of the three fragment types (regular, All-0, All-1).
* For DL errors, the amount of DL errors is saved in the `DL_ERRORS_{}` file in Google Cloud Storage. This file is not deleted when the Clean HTTP Request is sent from the LoPy4.

These parameters are put in the **Case X Fer X** for each case, duplicating the tab for these cases in RCZ4 and following the same format.

## Procedure

### FER 10%, no DL losses

Configure the callback in the following way:

```json
{
    "deviceType" : "01b29fc5",
    "device" : "{device}",
    "time" : "{time}",
    "data" : "{data}",
    "seqNumber" : "{seqNumber}",
    "ack" : "{ack}",
    "loss_rate" : 10,
    "enable_losses" : true,
    "enable_dl_losses" : false
}
```

Upload the project to the LoPy and execute it. After completing the 20 repetitions of the 70 bytes packets, the LoPy will ask for an input to continue with the 150 bytes packets, then the 231 bytes ones and finally the 512 bytes packets.

### FER 20%, no DL losses

Configure the callback in the following way:

```json
{
    "deviceType" : "01b29fc5",
    "device" : "{device}",
    "time" : "{time}",
    "data" : "{data}",
    "seqNumber" : "{seqNumber}",
    "ack" : "{ack}",
    "loss_rate" : 20,
    "enable_losses" : true,
    "enable_dl_losses" : false
}
```

Same functionality as above.

### FER 10% with DL losses

Configure the callback in the following way:

```json
{
    "deviceType" : "01b29fc5",
    "device" : "{device}",
    "time" : "{time}",
    "data" : "{data}",
    "seqNumber" : "{seqNumber}",
    "ack" : "{ack}",
    "loss_rate" : 10,
    "enable_losses" : true,
    "enable_dl_losses" : true
}
```

Same functionality as above.

### FER 20% with DL losses

Configure the callback in the following way:

```json
{
    "deviceType" : "01b29fc5",
    "device" : "{device}",
    "time" : "{time}",
    "data" : "{data}",
    "seqNumber" : "{seqNumber}",
    "ack" : "{ack}",
    "loss_rate" : 20,
    "enable_losses" : true,
    "enable_dl_losses" : true
}
```

Same functionality as above.