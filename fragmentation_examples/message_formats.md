# ACK Formats for SCHC-over-Sigfox

## Uplink ACK-on-Error Mode: Single-byte SCHC Header

The RECOMMENDED Fragmentation Header size is 8 bits, and it is composed as follows:
* RuleID size: 3 bits
* DTag size (T): 0 bits
* Window index (W) size (M): 2 bits
* Fragment Compressed Number (FCN) size (N): 3 bits
* MAX_ACK_REQUESTS: 5
* WINDOW_SIZE: 7 (with a maximum value of FCN=0b110)
* Tile size: 11 bytes
* Retransmission Timer: Application-dependent
* Inactivity Timer: Application-dependent
* RCS: Not used

```text
    
    |-- SCHC Fragment Header ----|
             |-- T --|-M-|-- N --|
    +-- ... -+- ... -+---+- ... -+~~~~~~~~~~~~~~~~~~~~+
    | Rule ID | Dtag | W |  FCN  | payload (11 bytes) |
    +-- ... -+- ... -+---+- ... -+~~~~~~~~~~~~~~~~~~~~+

```
```text
    Regular     : [ Rule ID | Dtag | W | FCN        | payload | (P-0) ]
    All-0       : [ Rule ID | Dtag | W | FCN(All-0) | payload | (P-0) ]
    All-1       : [ Rule ID | Dtag | W | FCN(All-1) | (payload) | (P-0) ]
    ACK REQ     : [ Rule ID | Dtag | W | FCN(All-0) | (P-0) ] -> Not implemented
    Sender Abort: [ Rule ID | Dtag | W | FCN(All-1) | (P-0) ]
```
How to differentiate an All-1 fragment with no payload from a Sender Abort.

The ACK size is 13 bits. Padding must be added to complete the 64 bits sigfox downlink maximum payload size.

```text
ACK Success: [ Rule ID | Dtag |   W  | C-1 | (P-0) ]
ACK Failure: [ Rule ID | Dtag |   W  | C-0 | Bitmap | (P-0) ]
Recv Abort : [ Rule ID | Dtag |  W-1 | C-1 | (P-1) ]
```
### Uplink ACK-on-Error Single-byte SCHC Header Message Examples
#### SCHC Receiver Abort message example:

The SCHC Receiver Abort message is 64 bits long.

```text
SCHC Receiver Abort
0001111111111111111111111111111111111111111111111111111111111111
```

* Rule ID: 000
* Dtag: not present
* W: 11
* C: 1 
* Padding: (58 bits) 1111111111111111111111111111111111111111111111111111111111

#### SCHC Sender Abort message example:

The SCHC Sender Abort message is 96 bits long.

```text
SCHC Sender Abort
000001110000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
```

* Rule ID: 000
* Dtag: not present
* W: 00 - (current window)
* FCN: 111 
* Padding: (88 bits) 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000


