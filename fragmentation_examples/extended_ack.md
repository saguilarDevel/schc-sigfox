

## Uplink ACK-on-Error Single-byte SCHC Header

The setting of Uplink ACK-on-Error Single-byte SCHC Header are:

* 300 bytes packet
* Tile size: 11 bytes
* Number of tiles: 28
* WINDOW_SIZE: 7 tiles
* Number of windows: 4 windows (00,01,10,11) 
* M:2 
* N:3
* bitmap size: 7 bits
* Rule ID: 000
* C bit: 1 bit

### ACK messages

#### SCHC-over-sigfox standard ACKs

In the ACK success format, the W field corresponds to the last received window and the C bit is set to 1.
In schc-over-sigfox DTAG is not present. 0 padding is added to complete the 64 bit Sigfox downlink frame size. 

```text
ACK Success: 
[ Rule ID | W | C-1 | (P-0) ]
   000     01    1     58 padding bits
```

In the failure ACK format the W field corresponds to the number of the smallest window with errors and the C bit is set to 0. 0 padding is added to complete the 64 bit downlinlk frame size.
```text
ACK Failure:
[ Rule ID | W | C-0 | Bitmap | (P-0) ]
    000    00    0   1111101    51 padding bits  
```

### Extended ACK

The Sigfox Donwlink frame is of a fixed size (64 bits), so padding must be added to the standard SCHC ACK format.
However, if the information about lost fragments of more windows are centralized in a single ACK, less donwlink messages are required, as a single ACK may centralize the complete information of the lost fragments of all windows. 

In Uplink ACK-on-Error Single-byte SCHC Header mode the size of M allows the use of 4 windows and a single ACK can acknowledged that 4 available windows, while carrying, for example, a 300-byte SCHC Packet.

The standard schc-over-sigfox failure ACK format is composed of a RuleID common for all the SCHC Packet. Then, each window is identify by its own set of values, such as the window number (W), the C bit and the bitmap. The success ACK format does not has any bitmap, therefore the extended ACK may have or not a bitmap when reporting a success reception of a given window.

Following are two proposal examples of extended ACK Formats.

#### Example Extended ACK format 1

In the extended ACK format 1, each window is identify by the combination of these two values: the window number and the C bit. 
For each window, when the C bit is set to 1, the bitmap is not present, meaning that no fragments where lost in that window. 
In case the C bit is set to 0, the 7-bit bitmap is added.

The example below shows the extended ACK format in a transmission of a 300-byte SCHC Packet with error in all transmission windows.
Note that a 300-byte SCHC Packet requires 4 transmission windows and 28 SCHC fragments. 

```text
Extended ACK format 1: 
[ Rule ID | W-0 | C-0 | Bitmap | W-1 | C-0 | Bitmap | W-2 | C-0 | Bitmap | W-3 | C-0 | Bitmap | (P-0)]
    000     00     0   1111011   01     0   1111101   10     0   1101111   11     0   1111011   21 padding bits

```
The example below shows the extended ACK format in a transmission of a 300-byte SCHC Packet with errors only in the first window.

```text
Extended ACK format 1: 
[ Rule ID | W | C-0 | Bitmap | W | C-1 | W | C-1 | W | C-1 | (P-0)]
    000    00    0   1111011  01    1   10    1   11    1    42 padding bits
```

The example below shows the extended ACK format in a transmission of a 300-byte SCHC Packet with errors only in the last window.

```text
Extended ACK format 1: 
[ Rule ID | W | C-1 | W | C-1 | W | C-1 | W | C-0 | Bitmap | (P-0)]
    000    00    1   01    1   10    1   11    0   1111011   42 padding bits
```


The example below shows the extended ACK format in a transmission of a 300-byte SCHC Packet with no error. All windows are acknowledged by setting the C-bit to 1. 

```text
Extended ACK format 1: 
[ Rule ID | W | C-1 | W | C-1 | W | C-1 | W | C-1 | (P-0)]
    000    00    1   01    1   10    1   11    1    49 padding bits

```

The example below shows the extended ACK format in a transmission of a 150-byte SCHC Packet. Note that a 150-byte SCHC Packet requires 2 transmission windows and 14 SCHC fragments.
When a SCHC Packet uses less than 4 windows, two options for the Extended ACK format are possible. 

1) Send information of all windows, even if no fragments are received.
2) Send only information about the windows received (as the sender knows how many windows are used).

#### 1. Send information of all windows

The 150-byte SCHC Packet only requires 2 window out of the 4 available. 
If, for example, there are error in both the first and second transmission window, the ACK will still have the information of the third and fourth window. 
This does not represent any issue, as the downlink frame must be of 64 bits.
Below is an example of the extended ACK format for a 150-byte SCHC Packet with errors in the first 2 windows. 
Note that the bitmap is added for windows 3 and 4, but with a bitmap of 0, as no fragment from that windows was received.

```text
Extended ACK format: 
[ Rule ID | W | C-0 | Bitmap | W | C-0 | Bitmap | W | C-0 | Bitmap | W | C-0 | Bitmap | (P-0)]
    000    00    0   1111011  01    0   1111101  10    0   0000000  11    0   0000000  41 padding bits
```

When all SCHC fragments are correctly received, the Extended ACK format will have the C bit equal to 1 in the first 2 windows.
```text
Extended ACK format: 
[ Rule ID | W | C-1 | W | C-1 | W | C-0 | Bitmap | W | C-0 | Bitmap | (P-0)]
    000    00    1   01    1   10    0   0000000  11    0   0000000  35 padding bits
```

Other option is to confirm that the SCHC Packet has been received completely by setting to 1 the C bit of all windows. 
```text
Extended ACK format: 
[ Rule ID | W | C-1 | W | C-1 | W | C-1 | W | C-1 | (P-0)]
    000    00    1   01    1   10    0   11    0    49 padding bits
```


#### 2. Send only information about the windows received

Following the example of the 150-byte SCHC Packet with errors in the first window, but in this case only two windows are present in the Extended ACK format, as shown below.

```text
Extended ACK format 1: 
[ Rule ID | W | C-0 | Bitmap | W | C-0 | Bitmap | (P-0)]
    000    00    0   1111011  01    0   1111101   41 padding bits
```

The example below shows the extended ACK format in a transmission of a 150-byte SCHC Packet with error in only one window.

```text
Extended ACK format 1: 
[ Rule ID | W | C-0 | Bitmap | W | C-1 | (P-0)]
    000    00    0   1111011  01    1      21 padding bits
```

The example below shows the extended ACK format in a transmission of a 150-byte SCHC Packet with no error.

```text
Extended ACK format 1: 
[ Rule ID | W | C-1 | W | C-1 | (P-0)]
    000    00    1   01    1    53 padding bits
```

Other option is to acknowledge the SCHC Packet is to send only the highest window numbered. 
The example below shows the extended ACK format in a transmission of a 150-byte SCHC Packet with no error and only acknowleding the highest window number.

```text
Extended ACK format 1: 
[ Rule ID | W | C-1 | (P-0)]
    000    10    1    58 padding bits
```

#### Example Extended ACK format 2

In the extended ACK format 2, each window is identify by the fix location in the ACK format, as the format is fixed for all cases.
The C bit and bitmap combination is present for the 4 windows, and no window number "W" is used. 
The C bit and bitmap for each window is identify by the position in the Extended ACK Format.
Note that the bitmap is always present.
 
The example below shows the extended ACK format 2 in a transmission of a 300-byte SCHC Packet with error in all transmission windows. 

```text
Extended ACK Format 2:
          |----- W-1 ----|----- W-2 ----|----- W-3 ----|----- W-4 ----| 
[ Rule ID | C-0 | Bitmap | C-0 | Bitmap | C-0 | Bitmap | C-0 | Bitmap | (P-0)]
    000      0   1111011    0   1111101    0   1111110    0   1111011   29 padding bits
   
```

The example below shows the extended ACK format in a transmission of a 300-byte SCHC Packet with errors only in the first window.

```text
Extended ACK Format 2:
          |----- W-1 ----|----- W-2 ----|----- W-3 ----|----- W-4 ----| 
[ Rule ID | C-0 | Bitmap | C-1 | Bitmap | C-1 | Bitmap | C-1 | Bitmap | (P-0)]
    000      0   1111011    1   1111111    1   1111111    1   1111111   29 padding bits
   
```

The example below shows the extended ACK format in a transmission of a 300-byte SCHC Packet with errors only in the last window.

```text
Extended ACK Format 2:
          |----- W-1 ----|----- W-2 ----|----- W-3 ----|----- W-4 ----| 
[ Rule ID | C-1 | Bitmap | C-1 | Bitmap | C-1 | Bitmap | C-0 | Bitmap | (P-0)]
    000      1   1111111    1   1111111    1   1111111    0   1011111   29 padding bits
   
```

The example below shows the extended ACK format in a transmission of a 300-byte SCHC Packet with no error. 

```text
Extended ACK Format 2:
          |----- W-1 ----|----- W-2 ----|----- W-3 ----|----- W-4 ----| 
[ Rule ID | C-1 | Bitmap | C-1 | Bitmap | C-1 | Bitmap | C-1 | Bitmap | (P-0)]
    000      1   1111111    1   1111111    1   1111111    1   1111111   29 padding bits
   
```

The example below shows the extended ACK format in a transmission of a 150-byte SCHC Packet with errors in the first 2 windows.

```text
Extended ACK Format 2:
          |----- W-1 ----|----- W-2 ----|----- W-3 ----|----- W-4 ----| 
[ Rule ID | C-0 | Bitmap | C-0 | Bitmap | C-0 | Bitmap | C-0 | Bitmap | (P-0)]
    000      0   1011111    0   1111011    0   0000000    0   0000000   29 padding bits
   
```

The example below shows the extended ACK format in a transmission of a 150-byte SCHC Packet with no errors.
There are 2 options:

1) Set to 1 only the C bit of the actually received windows.
```text
Extended ACK Format 2:
          |----- W-1 ----|----- W-2 ----|----- W-3 ----|----- W-4 ----| 
[ Rule ID | C-1 | Bitmap | C-1 | Bitmap | C-1 | Bitmap | C-1 | Bitmap | (P-0)]
    000      1   1111111    1   1111111    0   0000000    0   0000000   29 padding bits
   
```

2) Set to 1 all C bits as a confirmation that the SCHC Packet was correctly received.

```text
Extended ACK Format 2:
          |----- W-1 ----|----- W-2 ----|----- W-3 ----|----- W-4 ----| 
[ Rule ID | C-1 | Bitmap | C-1 | Bitmap | C-1 | Bitmap | C-1 | Bitmap | (P-0)]
    000      1   1111111    1   1111111    0   0000000    0   0000000   29 padding bits
   
```



### Transmission example comparison of 300-byte SCHC Packet with and without extended ACK
The example below shows the extended ACK format in a transmission of a 300-byte SCHC Packet with error in all transmission windows. 
Moreover, an example using the standard ACK format is presented for the same 300-byte SCHC Packet transmission.

#### Transmission of a 300-byte SCHC Packet with Extended ACK
In this example, instead of 4 downlink SCHC ACK, only 1 extended SCHC ACK is generated, reducing at lest 3 downlink messages (one for each window with errors except for the last one), when compared with the example using the standard ACK format. 
The last window will always generate an ACK.

```text
        Sender                      Receiver
          |-----W=0, FCN=6, Seq=1----->|
          |-----W=0, FCN=5, Seq=2----->|
          |-----W=0, FCN=4, Seq=3----->|
          |-----W=0, FCN=3, Seq=4----->|
          |-----W=0, FCN=2, Seq=5--X-->|
          |-----W=0, FCN=1, Seq=6----->|
          |-----W=0, FCN=0, Seq=7----->| Bitmap: 1111011
      (no ACK - no DL Enable)
          |-----W=1, FCN=6, Seq=8----->|
          |-----W=1, FCN=5, Seq=9----->|
          |-----W=1, FCN=4, Seq=10---->|
          |-----W=1, FCN=3, Seq=11---->|
          |-----W=1, FCN=2, Seq=12---->|
          |-----W=1, FCN=1, Seq=13-X-->|
          |-----W=1, FCN=0, Seq=14---->| Bitmap: 1111101
      (no ACK - no DL Enable)
          |-----W=2, FCN=6, Seq=15---->|
          |-----W=2, FCN=5, Seq=16---->|
          |-----W=2, FCN=4, Seq=17-X-->|
          |-----W=2, FCN=3, Seq=18---->|
          |-----W=2, FCN=2, Seq=19---->|
          |-----W=2, FCN=1, Seq=20---->|
          |-----W=2, FCN=0, Seq=21---->| Bitmap: 1101111
      (no ACK - no DL Enable)
          |-----W=3, FCN=6, Seq=22---->|
          |-----W=3, FCN=5, Seq=23---->|
          |-----W=3, FCN=4, Seq=24---->|
          |-----W=3, FCN=3, Seq=25---->|
          |-----W=3, FCN=2, Seq=26-X-->|
          |-----W=3, FCN=1, Seq=27---->|
DL Enable |-----W=3, FCN=7, Seq=28---->| Bitmap: 1111011
          |<---Extended ACK, Seq=28 ---| W=0, C=0, Bitmap:1111011 - W=1, C=0, Bitmap:1111101 - W=2, C=0, Bitmap:1101111 - W=3, C=0, Bitmap:1111011
          |-----W=0, FCN=2, Seq=30---->| W=0, C=1
          |-----W=1, FCN=1, Seq=31---->| W=1, C=1
          |-----W=2, FCN=4, Seq=32---->| W=2, C=1
          |-----W=3, FCN=2, Seq=33---->| W=3, C=1
DL Enable |-----W=3, FCN=7, Seq=34---->|
          |<---Extended ACK, Seq=35 ---| All W, C=1
        (End)
```

To request the ACK after retransmissions an All-1 message (Seq = 34) is sent.

#### Transmission of a 300-byte SCHC Packet without Extended ACK

The following is an example of a 300-byte SCHC Packet using the standard ACK format. 
Since there are fragment losses in all windows, and ACK is generated after the All-0 for intermediate windows.

```text
        Sender                      Receiver
          |-----W=0, FCN=6, Seq=1----->|
          |-----W=0, FCN=5, Seq=2----->|
          |-----W=0, FCN=4, Seq=3----->|
          |-----W=0, FCN=3, Seq=4----->|
          |-----W=0, FCN=2, Seq=5--X-->|
          |-----W=0, FCN=1, Seq=6----->|
DL Enable |-----W=0, FCN=0, Seq=7----->| Missing Fragment W=0, FCN=2, Seq=5
          |<------  ACK, Seq=8   ------| W=0, C=0, Bitmap: 1111011
          |-----W=0, FCN=2, Seq=9----->|
      (no ACK)
          |-----W=1, FCN=6, Seq=10---->|
          |-----W=1, FCN=5, Seq=11---->|
          |-----W=1, FCN=4, Seq=12---->|
          |-----W=1, FCN=3, Seq=13---->|
          |-----W=1, FCN=2, Seq=14---->|
          |-----W=1, FCN=1, Seq=15-X-->|
DL Enable |-----W=1, FCN=0, Seq=16---->| Missing Fragment W=1, FCN=1, Seq=15
          |<------  ACK, Seq=17  ------| W=1, C=0, Bitmap: 1111101
          |-----W=1, FCN=1, Seq=18---->|
      (no ACK)
          |-----W=2, FCN=6, Seq=19---->|
          |-----W=2, FCN=5, Seq=20---->|
          |-----W=2, FCN=4, Seq=21-X-->|
          |-----W=2, FCN=3, Seq=23---->|
          |-----W=2, FCN=2, Seq=24---->|
          |-----W=2, FCN=1, Seq=25---->| Missing Fragment W=2, FCN=4, Seq=21
DL Enable |-----W=2, FCN=0, Seq=26---->| Bitmap: 1101111
          |<------  ACK, Seq=27  ------| W=2, C=0, Bitmap: 1101111
          |-----W=2, FCN=4, Seq=28---->|
      (no ACK)
          |-----W=3, FCN=6, Seq=29---->|
          |-----W=3, FCN=5, Seq=30---->|
          |-----W=3, FCN=4, Seq=31---->|
          |-----W=3, FCN=3, Seq=32---->|
          |-----W=3, FCN=2, Seq=33-X-->|
          |-----W=3, FCN=1, Seq=34---->|
DL Enable |-----W=3, FCN=7, Seq=35---->| Bitmap: 1111011
          |<------  ACK, Seq=36  ------| W=3, C=0, Bitmap: 1111011
          |-----W=3, FCN=2, Seq=37---->| All fragments received
DL Enable |-----W=3, FCN=7, Seq=38---->|
          |<------ ACK, W=3, C=1 ------|
        (End)
```

Without the extended ACK format, after the All-0 message an ACK should be send, therefore
using the extended ACK format reduces, for example, one downlink message when error are present in 2
windows.

When errors are found in all windows, using extended ACK will reduce the number of ACKs. 
The ACK reduction can be calculated as the number of windows required for a SCHC Packet minus 1. 
For example, if the SCHC Packet requires 3 windows, and errors are found in all windows, without the extended ACK format there will be 2 All-0 messages that will generate an ACK.
With the extended ACK format, only the last ACK is generated, after the All-1 message is received. 
Therefore, the number of ACKs (not considering losses in retranmission) is reduced by the number of windows (3) - 1 = 2 ACKs.
As the packet size increases and the number of windows increases to 4, the reduction of ACKs increases to 3. 
SCHC Packet sizes that requires less than one window (less than 77 bytes) will see no benefit from using the Extended ACK format, as an ACK is always required after the last SCHC fragment (All-1 message).

