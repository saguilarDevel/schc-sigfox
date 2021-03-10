

## Uplink ACK-on-Error Single-byte SCHC Header

The settings of Uplink ACK-on-Error Single-byte SCHC Header are:

* Tile size: 11 bytes
* WINDOW_SIZE: 7 tiles
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

### Compound ACK

The Sigfox Donwlink frame is of a fixed size (64 bits), so padding must be added to the standard SCHC ACK format.
However, if the information about lost fragments of more windows are centralized in a single ACK, less donwlink messages are required, as a single ACK may centralize the complete information of the lost fragments of all windows. 

In Uplink ACK-on-Error Single-byte SCHC Header mode the size of M allows the use of 4 windows and a single ACK can acknowledged that 4 available windows, while carrying, for example, a 300-byte SCHC Packet.

The standard schc-over-sigfox failure ACK format is composed of a RuleID common for all the SCHC Packet. Then, each window is identify by its own set of values, such as the window number (W), the C bit and the bitmap. The success ACK format does not has any bitmap, therefore the extended ACK may have or not a bitmap when reporting a success reception of a given window.


#### Compound ACK format
Example of a 300-byte SCHC Packet.
* Number of tiles: 28
* Window_size = 7 tiles, 
* N = 3
* W = 2
* 300 bytes packet
* Number of windows: 4 windows (00,01,10,11) 

```text
Compound ACK Failure Format:
                    |-- W-0 --|---- W-1 ----|---- W-2 ----|---- W-3 ----| 
[ Rule ID | W | C-0 |  Bitmap | W |  Bitmap | W |  Bitmap | W |  Bitmap | (P-0)]
    000     00   0     1111011  01   1111101  10   1101111  11   1111011   24 padding bits
   
```
```text
Compound ACK Failure Format:
                    |-- W-0 --|---- W-1 ----|
[ Rule ID | W | C-0 |  Bitmap | W |  Bitmap | (P-0)]
    000     00   0     1111011  01   1111101   42 padding bits
   
```

```text
Compound ACK Failure Format:
                    |-- W-2 --|
[ Rule ID | W | C-0 |  Bitmap | (P-0)]
    000     10   0     1111011   51 padding bits
   
```

```text
Compound ACK Failure Format:
                    |-- W-2 --|---- W-3 ----|
[ Rule ID | W | C-0 |  Bitmap | W |  Bitmap | (P-0)]
    000     10   0     1111011  11   1111101   42 padding bits
   
```

```text
Compound ACK Failure Format:
                    |-- W-1 --|---- W-3 ----|
[ Rule ID | W | C-0 |  Bitmap | W |  Bitmap | (P-0)]
    000     01   0     1111011  11   1111101   42 padding bits
   
```

```text
Compound ACK Failure Format:
                    |-- W-1 --|---- W-3 ----|
[ Rule ID | W | C-0 |  Bitmap | W |  Bitmap | (P-0)]
    000     01   0     1111011  11   1111101   42 padding bits
   
```

```text
Compound ACK Failure Format:
                    |-- W-0 --|---- W-2 ----|---- W-3 ----| 
[ Rule ID | W | C-0 |  Bitmap | W |  Bitmap | W |  Bitmap | (P-0)]
    000     00   0     1111011  10   1111101  11   1111011   33 padding bits
   
```

```text
Compound ACK Failure Format:
                    |-- W-1 --|---- W-2 ----|---- W-3 ----| 
[ Rule ID | W | C-0 |  Bitmap | W |  Bitmap | W |  Bitmap | (P-0)]
    000     01   0     1111011  01   1111101  11   1111011   33 padding bits
   
```

```text
Compound ACK Failure Format:
                    |-- W-1 --|---- W-2 ----|---- W-3 ----| 
[ Rule ID | W | C-0 |  Bitmap | W |  Bitmap | W |  Bitmap | (P-0)]
    000     01   0     1111011  01   1111101  11   1111011   33 padding bits
   
```



#### Transmission of a 150-byte SCHC Packet without Compound ACK

The following is an example of a 150-byte SCHC Packet using 
the standard ACK format. 
Since there are fragment losses in all windows, 
an ACK is generated after the All-0 for intermediate windows.

* Number of tiles: 14
* Window_size = 7 tiles, 
* N = 3
* W = 2
* 150 bytes packet
* Number of windows: 2 windows (00,01) 

```text
        Sender                      Receiver
          |-----W=0, FCN=6, Seq=1----->|
          |-----W=0, FCN=5, Seq=2----->|
          |-----W=0, FCN=4, Seq=3----->|
          |-----W=0, FCN=3, Seq=4----->|
          |-----W=0, FCN=2, Seq=5--X-->|
          |-----W=0, FCN=1, Seq=6----->|
DL Enable |-----W=0, FCN=0, Seq=7----->| Missing Fragment W=0, FCN=2, Seq=5
          |<-- ACK, C=0, W=0, Seq=8  --| Bitmap: 1111011
          |-----W=0, FCN=2, Seq=9----->|
      (no ACK)
          |-----W=1, FCN=6, Seq=10---->|
          |-----W=1, FCN=5, Seq=11---->|
          |-----W=1, FCN=4, Seq=12---->|
          |-----W=1, FCN=3, Seq=13---->|
          |-----W=1, FCN=2, Seq=14---->|
          |-----W=1, FCN=1, Seq=15-X-->|
DL Enable |-----W=1, FCN=7, Seq=16---->| Missing Fragment W=1, FCN=1, Seq=15
          |<-- ACK, C=0, W=1, Seq=17 --| Bitmap: 1111101
          |-----W=1, FCN=1, Seq=18---->|
DL Enable |-----W=1, FCN=7, Seq=19---->| All fragments Received
          |<-- ACK, C=1, W=1, Seq=20 --|
        (End)
```


```text
        Sender              Receiver
          |-----W=0, FCN=6---->|
          |-----W=0, FCN=5---->|
          |-----W=0, FCN=4---->|
          |-----W=0, FCN=3---->|
          |-----W=0, FCN=2-X-->|
          |-----W=0, FCN=1---->|
DL Enable |-----W=0, FCN=0---->| 
          |<-- ACK, C=0, W=0 --| Bitmap: 1111011
          |-----W=0, FCN=2---->|
      (no ACK)
          |-----W=1, FCN=6---->|
          |-----W=1, FCN=5---->|
          |-----W=1, FCN=4---->|
          |-----W=1, FCN=3---->|
          |-----W=1, FCN=2---->|
          |-----W=1, FCN=1-X-->|
DL Enable |-----W=1, FCN=7---->| 
          |<-- ACK, C=0, W=1 --| Bitmap: 1111101
          |-----W=1, FCN=1---->|
DL Enable |-----W=1, FCN=7---->| All fragments received
          |<-- ACK, C=1, W=1 --|
        (End)
```

Without the compound ACK format, after the All-0 message an ACK is sent, 
therefore using a compound ACK format may reduce, for example, one downlink message when error are present in 2 windows (the ACK of the intermediate window).

When errors are found in all windows, using compound ACK will reduce the number of ACKs. 
The ACK reduction can be calculated as the number of windows required for a SCHC Packet minus 1. 
For example, if the SCHC Packet requires 3 windows, and errors are found in all windows, without the extended ACK format there will be 2 All-0 messages that will generate an ACK.
With the extended ACK format, only the last ACK is generated, after the All-1 message is received. 
Therefore, the number of ACKs (not considering losses in retranmission) is reduced by the number of windows (3) - 1 = 2 ACKs.
As the packet size increases and the number of windows increases to 4, the reduction of ACKs increases to 3. 
SCHC Packet sizes that requires less than one window (less than 77 bytes) will see no benefit from using the Extended ACK format, as an ACK is always required after the last SCHC fragment (All-1 message).





#### Transmission of a 150-byte SCHC Packet with Compound ACK
In this example, instead of 4 downlink SCHC ACK, only 1 compound SCHC ACK is generated, 
reducing at lest 1 downlink messages (one for each window with errors except for the last one), 
when compared with the example using the standard ACK format. 
The last window will always generate an ACK after the All-1 SCHC message.

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
DL Enable |-----W=1, FCN=7, Seq=14---->| Bitmap: 1111101
          |<--- Compund ACK, Seq=15 ---| W=0, Bitmap:1111011 - W=1, Bitmap:1111101
          |-----W=0, FCN=2, Seq=16---->| W=0 completed
          |-----W=1, FCN=1, Seq=17---->| W=1 completed
DL Enable |-----W=1, FCN=7, Seq=18---->|
          |<--- Success ACK, Seq=19 ---| W=1, C=1
        (End)
```


```text
        Sender              Receiver
          |-----W=0, FCN=6---->|
          |-----W=0, FCN=5---->|
          |-----W=0, FCN=4---->|
          |-----W=0, FCN=3---->|
          |-----W=0, FCN=2-X-->|
          |-----W=0, FCN=1---->|
          |-----W=0, FCN=0---->| Bitmap: 1111011
      (no ACK - no DL Enable)     
          |-----W=1, FCN=6---->|
          |-----W=1, FCN=5---->|
          |-----W=1, FCN=4---->|
          |-----W=1, FCN=3---->|
          |-----W=1, FCN=2---->|
          |-----W=1, FCN=1-X-->|
DL Enable |-----W=1, FCN=7---->| Bitmap: 1111101
          |<--- Compund ACK ---| W=0,1111011 - W=1,1111101
          |-----W=0, FCN=2---->| W=0 completed
          |-----W=1, FCN=1---->| W=1 completed
DL Enable |-----W=1, FCN=7---->|
          |<-- ACK, C=1, W=1 --|
        (End)
```
Compound ACK format

```text
Compound ACK Failure Format:
                    |-- W-0 --|---- W-1 ----|
[ Rule ID | W | C-0 |  Bitmap | W |  Bitmap | (P-0)]
    000     00   0     1111101  01   1111011   42 padding bits
   
```






### Transmission example comparison of 300-byte SCHC Packet with and without extended ACK
The example below shows the extended ACK format in a transmission of a 300-byte SCHC Packet with error in all transmission windows. 
Moreover, an example using the standard ACK format is presented for the same 300-byte SCHC Packet transmission.

#### Transmission of a 300-byte SCHC Packet with Compound ACK
In this example, instead of 4 downlink SCHC ACK, only 1 compound SCHC ACK is generated, reducing at lest 3 downlink messages (one for each window with errors except for the last one), when compared with the example using the standard ACK format. 
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
          |<---Compound ACK, Seq=28 ---| W=0, W=1, W=2, W=3
          |-----W=0, FCN=2, Seq=30---->| W=0 completed
          |-----W=1, FCN=1, Seq=31---->| W=1 completed
          |-----W=2, FCN=4, Seq=32---->| W=2 completed
          |-----W=3, FCN=2, Seq=33---->| W=3 completed
DL Enable |-----W=3, FCN=7, Seq=34---->|
          |<--- Success ACK, Seq=35 ---| C=1
        (End)
```

```text
        Sender              Receiver
          |-----W=0, FCN=6---->|
          |-----W=0, FCN=5---->|
          |-----W=0, FCN=4---->|
          |-----W=0, FCN=3---->|
          |-----W=0, FCN=2-X-->|
          |-----W=0, FCN=1---->|
          |-----W=0, FCN=0---->| Bitmap: 1111011
      (no ACK - no DL Enable)
          |-----W=1, FCN=6---->|
          |-----W=1, FCN=5---->|
          |-----W=1, FCN=4---->|
          |-----W=1, FCN=3---->|
          |-----W=1, FCN=2---->|
          |-----W=1, FCN=1-X-->|
          |-----W=1, FCN=0---->| Bitmap: 1111101
      (no ACK - no DL Enable)
        Sender              Receiver
          |-----W=2, FCN=6---->|
          |-----W=2, FCN=5---->|
          |-----W=2, FCN=4-X-->|
          |-----W=2, FCN=3---->|
          |-----W=2, FCN=2---->|
          |-----W=2, FCN=1---->|
          |-----W=2, FCN=0---->| Bitmap: 1101111
      (no ACK - no DL Enable)
          |-----W=3, FCN=6---->|
          |-----W=3, FCN=5---->|
          |-----W=3, FCN=4---->|
          |-----W=3, FCN=3---->|
          |-----W=3, FCN=2-X-->|
          |-----W=3, FCN=1---->|
DL Enable |-----W=3, FCN=7---->| Bitmap: 1111011
          |<---Compound ACK ---| W=0, W=1, W=2, W=3
          |-----W=0, FCN=2---->| W=0 completed
          |-----W=1, FCN=1---->| W=1 completed
          |-----W=2, FCN=4---->| W=2 completed
          |-----W=3, FCN=2---->| W=3 completed
DL Enable |-----W=3, FCN=7---->| All fragments received
          |<-- ACK, W=3, C=1 --| 
        (End)
```

To request the ACK after retransmissions an All-1 message (Seq = 34) is sent.

#### Transmission of a 300-byte SCHC Packet without Compound ACK

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
DL Enable |-----W=0, FCN=0, Seq=7----->| Missing Fragments 
          |<-- ACK, W=0, C=0, Seq=8 ---| Bitmap: 1111011
          |-----W=0, FCN=2, Seq=9----->|
      (no ACK)
          |-----W=1, FCN=6, Seq=10---->|
          |-----W=1, FCN=5, Seq=11---->|
          |-----W=1, FCN=4, Seq=12---->|
          |-----W=1, FCN=3, Seq=13---->|
          |-----W=1, FCN=2, Seq=14---->|
          |-----W=1, FCN=1, Seq=15-X-->|   
DL Enable |-----W=1, FCN=0, Seq=16---->| Missing Fragments
          |<-- ACK, W=1, C=0, Seq=17 --| Bitmap: 1111101
          |-----W=1, FCN=1, Seq=18---->|
      (no ACK)
          |-----W=2, FCN=6, Seq=19---->|
          |-----W=2, FCN=5, Seq=20---->|
          |-----W=2, FCN=4, Seq=21-X-->|
          |-----W=2, FCN=3, Seq=23---->|
          |-----W=2, FCN=2, Seq=24---->|
          |-----W=2, FCN=1, Seq=25---->| 
DL Enable |-----W=2, FCN=0, Seq=26---->| Missing Fragments
          |<-- ACK, W=2, C=0, Seq=27 --| Bitmap: 1101111
          |-----W=2, FCN=4, Seq=28---->|
      (no ACK)
          |-----W=3, FCN=6, Seq=29---->|
          |-----W=3, FCN=5, Seq=30---->|
          |-----W=3, FCN=4, Seq=31---->|
          |-----W=3, FCN=3, Seq=32---->|
          |-----W=3, FCN=2, Seq=33-X-->|
          |-----W=3, FCN=1, Seq=34---->|
DL Enable |-----W=3, FCN=7, Seq=35---->| Missing Fragments
          |<-- ACK, W=3, C=0, Seq=36 --| Bitmap: 1111011
          |-----W=3, FCN=2, Seq=37---->| All fragments received
DL Enable |-----W=3, FCN=7, Seq=38---->|
          |<------ ACK, W=3, C=1 ------| 
        (End)
```


```text
        Sender              Receiver
          |-----W=0, FCN=6---->|
          |-----W=0, FCN=5---->|
          |-----W=0, FCN=4---->|
          |-----W=0, FCN=3---->|
          |-----W=0, FCN=2-X-->|
          |-----W=0, FCN=1---->| 
DL Enable |-----W=0, FCN=0---->| 
          |<-- ACK, W=0, C=0 --| Bitmap: 1111011
          |-----W=0, FCN=2---->|
      (no ACK)
          |-----W=1, FCN=6---->|
          |-----W=1, FCN=5---->|
          |-----W=1, FCN=4---->|
          |-----W=1, FCN=3---->|
          |-----W=1, FCN=2---->|
          |-----W=1, FCN=1-X-->|   
DL Enable |-----W=1, FCN=0---->| 
          |<-- ACK, W=1, C=0 --| Bitmap: 1111101
          |-----W=1, FCN=1---->|
      (no ACK)
        Sender              Receiver
          |-----W=2, FCN=6---->|
          |-----W=2, FCN=5---->|
          |-----W=2, FCN=4-X-->|
          |-----W=2, FCN=3---->|
          |-----W=2, FCN=2---->|
          |-----W=2, FCN=1---->| 
DL Enable |-----W=2, FCN=0---->| 
          |<-- ACK, W=2, C=0 --| Bitmap: 1101111
          |-----W=2, FCN=4---->|
      (no ACK)
          |-----W=3, FCN=6---->|
          |-----W=3, FCN=5---->|
          |-----W=3, FCN=4---->|
          |-----W=3, FCN=3---->|
          |-----W=3, FCN=2-X-->|
          |-----W=3, FCN=1---->|
DL Enable |-----W=3, FCN=7---->| 
          |<-- ACK, W=3, C=0 --| Bitmap: 1111011
          |-----W=3, FCN=2---->| All fragments received
DL Enable |-----W=3, FCN=7---->|
          |<-- ACK, W=3, C=1 --| 
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




---------
150-bytes SCHC Packet 

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
          |<---Extended ACK, Seq=28 ---| W=0, Bitmap:1111011 - W=1, Bitmap:1111101 - W=2, Bitmap:1101111 - W=3, Bitmap:1111011
          |-----W=0, FCN=2, Seq=30---->| W=0 completed
          |-----W=1, FCN=1, Seq=31---->| W=1 completed
          |-----W=2, FCN=4, Seq=32---->| W=2 completed
          |-----W=3, FCN=2, Seq=33---->| W=3 completed
DL Enable |-----W=3, FCN=7, Seq=34---->|
          |<---Extended ACK, Seq=35 ---| All W, C=1
        (End)
```






Window_size = 15 tiles, N = 4, W = 2


```text
Compound ACK Failure Format 3:
                    |------- W-0 -------|--------- W-1 ---------|--------- W-2 ---------| 
[ Rule ID | W | C-0 |       Bitmap      | W |       Bitmap      | W |       Bitmap      | (P-0)]
    000     00   0     111101111111011    01   111101111011111    10    111101111011101    9 padding bits
   
```

```text
Compound ACK Failure Format 3:
                    |------- W-0 -------|--------- W-2 ---------|
[ Rule ID | W | C-0 |       Bitmap      | W |       Bitmap      | (P-0)]
    000     00   0     111101111111011    10   111101111011111     26 padding bits
   
```

```text
Compound ACK Failure Format 3:
                    |------- W-2 -------|--------- W-3 ---------|
[ Rule ID | W | C-0 |       Bitmap      | W |       Bitmap      | (P-0)]
    000     10   0     111101111111011    11   111101111011111     26 padding bits
   
```


```text
Compound ACK Failure Format 3:
                    |------- W-1 -------|--------- W-3 ---------|
[ Rule ID | W | C-0 |       Bitmap      | W |       Bitmap      | (P-0)]
    000     01   0     111101111111011    11   111101111011111     26 padding bits
   
```

```text
Compound ACK Failure Format 3:
                    |------- W-0 -------|--------- W-3 ---------|
[ Rule ID | W | C-0 |       Bitmap      | W |       Bitmap      | (P-0)]
    000     00   0     111101111111011    11   111101111011111     26 padding bits
   
```


