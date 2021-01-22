

## Uplink ACK-on-Error Single-byte SCHC Header

300 bytes packet
Tile size: 11 bytes
Number of tiles: 28
WINDOW_SIZE: 7 tiles
Number of windows: 4 windows (00,01,10,11)
bitmap size: 7 bits
Rule ID: 000
C bit: 

### ACK messages

SCHC standard ACK
```text
ACK Failure:
[ Rule ID | W | C-0 | Bitmap | (P-0) ]
    000    00    0   1111101    51 padding bits  
```

Errors in one window
```text
ACK Failure: 
[ Rule ID | W | C-0 | Bitmap | (P-0)]
    000    00    0   1111011    51 padding bits
    0000001111011000000000000000000000000000000000000000000000000000
```
Errors in two windows
```text
ACK Failure: 
[ Rule ID | W | C-0 | Bitmap | W | C-0 | Bitmap | (P-0)]
    000    00    0   1111011  01    0   1111101   41 padding bits
    0000001111011010111110100000000000000000000000000000000000000000
```
Errors in three windows
```text
ACK Failure: 
[ Rule ID | W | C-0 | Bitmap | W | C-0 | Bitmap | W | C-0 | Bitmap | (P-0)]
    000    00    0   1111011  01    0   1111101  10    0   1111110    31 padding bits
    0000001111011010111110110011111100000000000000000000000000000000  

```
Error in four windows
```text
ACK Failure: 
[ Rule ID | W | C-0 | Bitmap | W | C-0 | Bitmap | W | C-0 | Bitmap | W | C-0 | Bitmap | (P-0)]
    000    00    0   1111011  01    0   1111101  10    0   1111110   11   0   1111011   21 padding bits
    000    00    0   1111011  01    0   1111101  10    0   1111110   11   0   1111011
    0000001111011010111110110011111101101111011000000000000000000000
```

Note that, the windows are numbered from the lowest window number 
with errors to the last.
```text
ACK Failure: 
[ Rule ID | W | C-0 | Bitmap | W | C-0 | Bitmap | W | C-0 | Bitmap | W | C-0 | Bitmap | (P-0)]
    000    00    0   1111011  01    0   1111101  10    0   1111110   11   0   1111011   21 padding bits
    000    00    0   1111011  01    0   1111101  10    0   1111110   11   0   1111011
    0000001111011010111110110011111101101111011000000000000000000000
```

### Transmission example

```text
        Sender                      Receiver
          |-----W=0, FCN=6, Seq=1----->|
          |-----W=0, FCN=5, Seq=2----->|
          |-----W=0, FCN=4, Seq=3--X-->|
          |-----W=0, FCN=3, Seq=4----->|
          |-----W=0, FCN=2, Seq=5----->|
          |-----W=0, FCN=1, Seq=6----->|
DL Enable |-----W=0, FCN=0, Seq=7----->|
      (no ACK)
          |-----W=1, FCN=6, Seq=8----->|
          |-----W=1, FCN=5, Seq=9--X-->|
          |-----W=1, FCN=4, Seq=10---->|
DL Enable |-----W=1, FCN=7, Seq=11---->| Missing Fragment W=0, FCN=4, Seq=3, W=1, FCN=5, Seq=9
          |<------      ACK,     ------|  W=0, C=0, Bitmap:1101111 - W=1, C=0, Bitmap:1010001
          |-----W=0, FCN=3, Seq=12---->| 
          |-----W=1, FCN=5, Seq=13---->| All fragments received
DL Enable |-----W=1, FCN=7, Seq=14---->| All fragments received
          |<------ ACK, W=1, C=1 ------| Highest number W, C=1
        (End)
```

Without extended ACK, after the All-0 message an ACK should be send, therefore
using extended ACK reduces one downlink message when error are present in 2
windows.

When errors are found in all windows, using extended ACK will reduce the 
number of ACKs in number of windows - 1. For example, for 3 windows, errors
in all windows, without extended ACK, there will be 2 All-0 messages
generating ACKs. With extended ACK, there is only the last ACK generated with 
the All-1 message. Therefore, the number of ACKs (before retranmission) is reduced
in the number of windows (3) - 1 = 2 ACKs.


### ACK examples

Less than 77 bytes, only one window

SCHC standard ACK
```text
ACK Failure:
[ Rule ID | W | C-0 | Bitmap | (P-0) ]
    000    00    0   1111101    51 padding bits  
```


Packet sizes between 78 bytes and 154 bytes, two windows

```text
ACK Failure: 
[ Rule ID | W | C-0 | Bitmap | W | C-0 | Bitmap | (P-0)]
    000    00    0   1111011  01    0   1111101   41 padding bits
    0000001111011010111110100000000000000000000000000000000000000000
```


Packet sizes between 155 bytes and 231 bytes, three windows

```text
ACK Failure: 
[ Rule ID | W | C-0 | Bitmap | W | C-0 | Bitmap | W | C-0 | Bitmap | (P-0)]
    000    00    0   1111011  01    0   1111101  10    0   1111110    31 padding bits
    0000001111011010111110110011111100000000000000000000000000000000  

```

Packet sizes between 232 bytes and 300 bytes, four windows

```text
ACK Failure: 
[ Rule ID | W | C-0 | Bitmap | W | C-0 | Bitmap | W | C-0 | Bitmap | W | C-0 | Bitmap | (P-0)]
    000    00    0   1111011  01    0   1111101  10    0   1111110   11   0   1111011   21 padding bits
    000    00    0   1111011  01    0   1111101  10    0   1111110   11   0   1111011
    0000001111011010111110110011111101101111011000000000000000000000
```


### Possible use cases.

300 bytes packet
Tile size: 11 bytes
Number of tiles: 28
WINDOW_SIZE: 7 tiles
Number of windows: 4 windows (00,01,10,11)
bitmap size: 7 bits
Rule ID: 000
C bit: 

Rule ID 00

Less than 77 bytes, only one window

Rule ID 01

Packet sizes between 78 bytes and 154 bytes, two windows

Rule ID 01

Packet sizes between 155 bytes and 231 bytes, three windows

Rule ID 11

Packet sizes between 232 bytes and 300 bytes, four windows
