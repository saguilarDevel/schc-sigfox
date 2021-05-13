
# Compound ACK

In order to take an efficient use of the downlink channel, a SCHC Compound ACK (MAY or MUST)  be sent when SCHC bidirectional services (e.g., ACK-on-Error fragmentation mode) are used. 
The SCHC Compound ACK is intended to reduce the number of downlink  transmissions (e.g., SCHC ACKs) by accumulating bitmaps of several windows in a single SCHC message (i.e., the SCHC Compound ACK). 
The SCHC Compound ACK extends the SCHC ACK message format so that it can contain several bitmaps, each bitmap being identified by its corresponding window number.

The SCHC Compound ACK:
* provides feedback only for windows with fragment losses,
 * has a variable size that depends on the number of windows with fragment losses being reported in the single Compound SCHC ACK,
 * includes the window number (i.e., W) of each bitmap,
 * has a format coincident with that of a SCHC ACK (RFC 8724) when only one window with losses is reported,
 * might not cover all windows with fragment losses of a SCHC Packet,
 * is distinguishable from the SCHC Receiver-Abort.

The SCHC Compound ACK groups the window number (W) with its corresponding bitmap.
 The window number and its bitmap MUST be ordered from the lowest-numbered to the highest-numbered window. 


# SCHC-over-Sigfox F/R Message Formats
This section defines the SCHC Fragment formats, the SCHC ACK formats, including the SCHC Compound ACK, and the SCHC Abort formats used in SCHC over Sigfox.

## Uplink ACK-on-Error Mode: Single-byte SCHC Header

### SCHC Fragment Formats

#### Regular SCHC Frgment
Figure 1 shows an example of a regular SCHC fragment for all fragments except the last one. 
As tiles are of 11 bytes, padding MUST NOT be added.


```text
    
   |-- SCHC Fragment Header --|
   + ------------------------ + ------- +
   | RuleID |   W    | FCN    | Payload |
   + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 3 bits | 88 bits |
        Figure 1: Regular SCHC Fragment format for all fragments except the last one

```

The SCHC ACK REQ SHOULD NOT be used, instead the All-1 SCHC Fragment MUST be used to request a SCHC ACK from the receiver (Network SCHC). 
As per RFC8724, the All-0 message is distinguishable from the SCHC ACK REQ (All-1 message). 
The penultimate tile of a SCHC Packet is of regular size.

#### All-1 SCHC Fragment

Figure 2 shows an example of the All-1 message. 
The All-1 message MUST contain the last tile of the SCHC Packet. 
The last tile MUST be of at least 1 byte (one L2 word). 
Padding MUST NOT be added, as the resulting size is L2-word-multiple.

```text
    
   |---  SCHC Fragment Header ---|
   + --------------------------- + ------------ + 
   | RuleID |   W    | FCN=ALL-1 |    Payload   |
   + ------ + ------ + --------- + ------------ +
   | 3 bits | 2 bits |  3 bits   | 8 to 88 bits |

        Figure 2: All-1 SCHC Message format with last tile

```

As per RFC8724 the All-1 must be distinguishable from the a SCHC Sender-Abort message (with same Rule ID, M and N values). 
The All-1 MUST have the last tile of the SCHC Packet, that MUST be of at least 1 byte. 
The SCHC Sender-Abort message header size is of 1 byte, with no padding bits.

*How these message are distinguishable?*

What happens with a payload of zeros (0) or ones (1) in All-1?
For the All-1 message to be distinguishable from the Sender-Abort message, the Sender-Abort message MUST be of 1 byte (only header with no padding).
This way, the minimum size of the All-1 is 3 bytes, and the Sender-Abort message is of 2 bytes.

#### SCHC ACK Format

Figure 3 shows the SCHC ACK format when all fragments have been correctly received (C=1). 
Padding MUST be added to complete the 88-bit Sigfox downlink frame payload size.

```text
    
   |---- SCHC ACK Header ----|
   + ----------------------- + ------- +
   | RuleID |    W   | C=b'1 | b'0-pad |
   + ------ + ------ + ----- + ------- +
   | 3 bits | 2 bits | 1 bit | 58 bits |
        Figure 3: SCHC Success ACK message format. 
```

In case SCHC fragment losses are found in any of the windows of the SCHC Packet (C=0), the SCHC Compound ACK MUST be used.
 The SCHC Compound ACK message format is shown in Figure 4.
  The window numbered 00, if present in the SCHC Compound ACK, MUST be placed between the Rule ID and the C bit to avoid confusion with padding bits.  
  If padding is needed for the SCHC Compound ACK, padding bits MUST be 0 to make subsequent window numbers and bitmaps distinguishable.


```text
    
   |---- SCHC ACK Header ----|-W = x -| ... | --- W = x + i ---|
   + ----------------------- + ------ + ... + ------- + ------ + ------- +
   | RuleID | W=b'x  | C=b'0 | Bitmap | ... | W=b'x+i | Bitmap | b'0-pad |
   + ------ + ------ + ----- + ------ + ... + ------- + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits |     | 2 bits | 7 bits |
        Figure 4: SCHC Compound ACK message format. 
        On top are noted the window number of the corresponding bitmap. 
        Losses are found in windows x,...,x+i.
```


Following figures are examples of the Compound ACK message format.

```text
    
   |---- SCHC ACK Header ----|- W=00 -|----- W=01 ------|
   + ----------------------- + ------ + ------ + ------ + ------- +
   | RuleID | W=b'00 | C=b'0 | Bitmap | W=b'01 | Bitmap | b'0-pad |
   + ------ + ------ + ----- + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 42 bits |
        Figure 5: SCHC Compound ACK example. 
        On top are noted the window number of the corresponding bitmap.
        Losses are found in windows 0 and 1. 
```

```text
    
   |---- SCHC ACK Header ----|- W=01 -|----- W=11 ------|
   + ----------------------- + ------ + ------ + ------ + ------- +
   | RuleID | W=b'01 | C=b'0 | Bitmap | W=b'11 | Bitmap | b'0-pad |
   + ------ + ------ + ----- + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 42 bits |
        Figure 6: SCHC Compound ACK example.
        Losses are found in windows 0 and 1.

```


```text
   |---- SCHC ACK Header ----|- W=00 -|----- W=10 ------|
   + ----------------------- + ------ + ------ + ------ + ------- +
   | RuleID | W=b'00 | C=b'0 | Bitmap | W=b'10 | Bitmap | b'0-pad |
   + ------ + ------ + ----- + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 42 bits |
        Figure 7: SCHC Compound ACK example 
        Losses are found in windows 0 and 1.
```

Figure 8 shows the Compound ACK message format when losses are found in all windows.
The window numbers and its corresponding bitmaps are ordered from window numbered 00 to 11, notifying all four possible windows.

```text
    
   |---- SCHC ACK Header ----|-W=b'00-|---- W=b'01 -----|---- W=b'10 -----|---- W=b'11 -----|
   + ----------------------- + ------ + ------ + ------ + ------ + ------ + ------ + ------ + ------- +
   | RuleID | W=b'00 | C=b'0 | Bitmap | W=b'01 | Bitmap | W=b'10 | Bitmap | W=b'11 | Bitmap | b'0-pad |
   + ------ + ------ + ----- + ------ + ------ + ------ + ------ + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 2 bits | 7 bits | 2 bits | 7 bits | 24 bits |
        Figure 8: SCHC Compound ACK example
        Losses are found in windows 0, 1, 2 and 3. 
```


```text
    
   |---- SCHC ACK Header ----|-W=b'00-|---- W=b'01 -----|---- W=b'10 -----|
   + ----------------------- + ------ + ------ + ------ + ------ + ------ + ------- +
   | RuleID | W=b'00 | C=b'0 | Bitmap | W=b'01 | Bitmap | W=b'10 | Bitmap | b'0-pad |
   + ------ + ------ + ----- + ------ + ------ + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 2 bits | 7 bits | 33 bits |
        Figure 9: SCHC Compound ACK example 
        Losses are found in 0, 1 and 2.
```

#### SCHC Sender-Abort Message formats


```text
    
   |---- Sender-Abort Header ----|
   + --------------------------- +
   | RuleID |   W    | FCN=ALL-1 |
   + ------ + ------ + --------- +
   | 3 bits | 2 bits |  3 bits   |

        Figure 10.1: SCHC Sender-Abort message format
```

```text
    
   |---- Sender-Abort Header ----|
   + --------------------------- + ------- +
   | RuleID |   W    | FCN=ALL-1 | b'0-pad |
   + ------ + ------ + --------- + ------- +
   | 3 bits | 2 bits |  3 bits   | 88 bits |

        Figure 10.2: SCHC Sender-Abort message format with padding
        OLD FORMAT
```

#### SCHC Receiver-Abort Message formats

```text
    
   |- Receiver-Abort Header -|
   + ----------------------- + ------- +
   | RuleID | W=b'11 | C=b'1 | b'1-pad |
   + ------ + ------ + ----- + ------- +
   | 3 bits | 2 bits | 1 bit | 58 bits |
        Figure 11: SCHC Receiver-Abort message format.
```

## Uplink ACK-on-Error Mode: Two-byte SCHC Header

### SCHC Fragment Formats

#### Regular SCHC Fragment
Figure 12 shows an example of a regular SCHC fragment for all fragments except the last one.
The penultimate tile of a SCHC Packet is of the regular size.

```text
    
   |-- SCHC Fragment Header --|
   + ------------------------ + ------- +
   | RuleID |   W    | FCN    | Payload |
   + ------ + ------ + ------ + ------- +
   | 8 bits | 3 bits | 5 bits | 80 bits |
        Figure 12: Regular SCHC Fragment format for all fragments except the last one
```

The SCHC ACK REQ SHOULD NOT be used, instead the All-1 SCHC Fragment MUST be used to request a SCHC ACK from the receiver (Network SCHC).
As per RFC8724, the All-0 message is distinguishable from the SCHC ACK REQ (All-1 message)

#### All-1 SCHC Fragment

Figure 13 shows an example of the All-1 message. 
The All-1 message MUST contain the last tile of the SCHC Packet.

```text
    
   |---  SCHC Fragment Header ---|
   + --------------------------- + ------------ +
   | RuleID |   W    | FCN=ALL-1 |    Payload   |
   + ------ + ------ + --------- + ------------ +
   | 8 bits | 3 bits |  5 bits   | 8 to 80 bits |

        Figure 13: All-1 SCHC message format with last tile
```

As per RFC8724 the All-1 must be distinguishable from the a SCHC Sender-Abort message (with same Rule ID, M and N values).
The All-1 MUST have the last tile of the SCHC Packet, that MUST be of at least 1 byte. 
The SCHC Sender-Abort message header size is of 2 byte, with no padding bits.

*How these message are distinguishable?*
For the All-1 message to be distinguishable from the Sender-Abort message, the Sender-Abort message MUST be of 2 byte (only header with no padding).
This way, the minimum size of the All-1 is 3 bytes, and the Sender-Abort message is of 2 bytes.

#### SCHC ACK Format

Figure 14 shows the SCHC ACK format when all fragments have been correctly received (C=1). 
Padding MUST be added to complete the 88-bit Sigfox downlink frame payload size.

```text
    
   |----- SCHC ACK Header ----|
   + ------------------------ + ------- +
   | RuleID |    W   | C=b'1 | b'0-pad |
   + ------ + ------ + ----- + ------- +
   | 8 bits |  3 bits | 1 bit | 52 bits |
        Figure 14: SCHC Success ACK message format.  
```

The SCHC Compound ACK message (MAY or MUST) be used in case SCHC fragment losses are found in any window of the SCHC Packet (C=0).
The SCHC Compound ACK message format is shown in Figure 15.
The SCHC Compound ACK can report up to 3 windows with losses.
The window number (W) and its corresponding bitmap MUST be ordered from the lowest-numbered window number to the highest-numbered window.
If window numbered 000 is present in the SCHC Compound ACK, the window number 000 MUST be placed between the Rule ID and C bit to avoid confusion with padding bits.
The SCHC Compound ACK MUST be 0 padded (Padding bits must be 0).


```text
    
   |----- SCHC ACK Header ----|- W=b'x -| ... |----- W=b'x+i -----|
   + ------------------------ + ------- + ... + ------- + ------- + ------- +
   | RuleID |  W=b'x  | C=b'0 |  Bitmap | ... | W=b'x+i |  Bitmap | b'0-pad |
   + ------ + ------- + ----- + ------- + ... | ------- + ------- + ------- +
   | 8 bits |  3 bits | 1 bit | 15 bits | ... |  3 bits | 15 bits |
        Figure 15: SCHC Compound ACK message format. 
        On top are noted the window number of the corresponding bitmap. 
        Losses are found in windows x,...,x+i. 
```


#### SCHC Sender-Abort Messages

```text
    
   |---- Sender-Abort Header ----|
   + --------------------------- + 
   | RuleID |   W    | FCN=ALL-1 |
   + ------ + ------ + --------- +
   | 8 bits | 3 bits |  5 bits   |
        Figure 16.1: SCHC Sender-Abort message format
```
```text
    
   |---- Sender-Abort Header ----|
   + --------------------------- + ------- +
   | RuleID |   W    | FCN=ALL-1 | b'0-pad |
   + ------ + ------ + --------- + ------- +
   | 8 bits | 3 bits |  5 bits   | 80 bits |

        Figure 16.2: SCHC Sender-Abort message format with padding
        (OLD FORMAT)
```


#### SCHC Receiver-Abort Message

```text
    
   |-- Receiver-Abort Header -|
   + ------------------------ + ------- +
   | RuleID | W=b'111 | C=b'1 | b'1-pad |
   + ------ + ------- + ----- + ------- +
   | 8 bits |  3 bits | 1 bit | 58 bits |
        Figure 17: SCHC Receiver-Abort message format.
```
