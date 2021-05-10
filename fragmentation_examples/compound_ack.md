
# Compound ACK

To take maximum advantages of downlink tranmissions, a SCHC Compound ACK MUST be sent when SCHC bi-directional services (e.g. ACK-on-Error fragmentation mode) are used. 
The SCHC Compound ACK reduces the number of donwlink transmission (e.g. SCHC ACKs) by accumulating bitmaps of several windows in a single SCHC Compound ACK. 
The SCHC Compound ACK substitutes the SCHC ACK failure message format, by extending its format to contain additional bitmaps, with its corresponding window number.

The SCHC Compound ACK:
* report only windows with fragment losses,
* includes the window number of each bitmap (i.e. W and bitmap groups),
* reports at least one window with fragment losses (i.e., if only one window with losses is reported in the SCHC Compound ACK, the SCHC ACK will the have the same format as in RFC8724),
* MAY not report all windows with fragment losses of a SCHC Packet,
* has a variable size, that depends on the number of windows with fragment losses being reported in the single Compound SCHC ACK,
* is distinguishable of the SCHC Receiver-Abort.

The SCHC Compound ACK uses W and bitmap groups.
 The W and bitmaps groups MUST be ordered from the lowest-numbered window number to the highest-numbered window.
The window numbered 00 if present in the SCHC Compound ACK MUST be placed between the Rule ID and C bit to avoid confusion with padding bits.
The Compound ACK MUST be 0 padded (Padding bits must be 0) to make distinguishable subsequents windows numbers and bitmaps groups.



# SCHC-over-Sigfox F/R Message Formats
This section defines the SCHC fragment formats, the SCHC ACK format, including the SCHC Compound ACK, and the SCHC Abort formats.

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

The SCHC ACK REQ is not used, instead the All-1 SCHC Fragment MUST be used. 
As per RFC8724, the All-0 message is distinguishable from the SCHC ACK REQ (All-1 message).
The penultimate tile of a SCHC Packet is of the regular size.

#### All-1 SCHC Fragment

Figure 2 shows an example of the All-1 message. 
The All-1 message MUST contain the last tile of the SCHC Packet.
The last tile MUST be of at least 1 byte (one L2 word). 
Padding MUST NOT be added, as the resulting size is a L2 word multiple.

```text
    
   |---  SCHC Fragment Header ---|
   + --------------------------- + ------------ + 
   | RuleID |   W    | FCN=ALL-1 |    Payload   |
   + ------ + ------ + --------- + ------------ +
   | 3 bits | 2 bits |  3 bits   | 8 to 88 bits |

        Figure 2: All-1 SCHC Message with last tile

```

As per RFC8724 the All-1 must be distinguishable from the a SCHC Sender-Abort message (with same Rule ID, M and N values). 
The All-1 MUST have the last tile of the SCHC Packet, that MUST be of at least 1 byte. 
The SCHC Sender-Abort message header size is of 1 byte, with no padding bits.





***Review how the message are distinguishable***
What happens with a payload of zeros (0) or ones (1) in All-1?

For the All-1 message to be distinguishable from the Sender-Abort message, the Sender-Abort message MUST be of 1 byte (only header with no padding).
This way, the minimum size of the All-1 is 3 bytes, and the Sender-Abort message is of 2 bytes.

#### SCHC ACK Format

Figure 3 shows the SCHC ACK format when all fragments have been correctly received (C=1).
Padding MUST be added to complete the 88 bits Sigfox donwlink payload size.

```text
    
   |---- SCHC ACK Header ----|
   + ----------------------- + ------- +
   | RuleID | W=b'00 | C=b'1 | b'0-pad |
   + ------ + ------ + ----- + ------- +
   | 3 bits | 2 bits | 1 bit | 58 bits |
        Figure 3: SCHC Success ACK format. 
```

In case SCHC fragment losses are found in any windows (C=0), the SCHC Compound ACK MUST be used for the ACK failure messages.
The SCHC Compound ACK message is shown in Figure 4.




```text
    
   |---- SCHC ACK Header ----|- W=00 -|----- W=01 ------|
   + ----------------------- + ------ + ------ + ------ + ------- +
   | RuleID | W=b'00 | C=b'0 | Bitmap | W=b'01 | Bitmap | b'0-pad |
   + ------ + ------ + ----- + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 42 bits |
        Figure 4: SCHC Compound ACK format. 
        On top are noted the window of each window number and bitmap group. 
        Losses are found in windows 0 and 1. 
```

Following figures are examples of the Compound ACK message format.

```text
    
   |---- SCHC ACK Header ----|- W=01 -|----- W=11 ------|
   + ----------------------- + ------ + ------ + ------ + ------- +
   | RuleID | W=b'01 | C=b'0 | Bitmap | W=b'11 | Bitmap | b'0-pad |
   + ------ + ------ + ----- + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 42 bits |
        Figure 5: SCHC Compound ACK format with losses in windows 1 and 3 

```

```text
    
   |---- SCHC ACK Header ----|- W=00 -|----- W=10 ------|
   + ----------------------- + ------ + ------ + ------ + ------- +
   | RuleID | W=b'00 | C=b'0 | Bitmap | W=b'10 | Bitmap | b'0-pad |
   + ------ + ------ + ----- + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 42 bits |
        Figure 6: SCHC Compound ACK format with losses in windows 1 and 3 

```

Figure 7 shows the Compound ACK message format when losses are found in all windows.
The window and bitmap groups are ordered from window numbered 00 to 11, notifying all four possible windows.

```text
    
   |---- SCHC ACK Header ----|-W=b'00-|---- W=b'01 -----|---- W=b'10 -----|---- W=b'11 -----|
   + ----------------------- + ------ + ------ + ------ + ------ + ------ + ------ + ------ + ------- +
   | RuleID | W=b'00 | C=b'0 | Bitmap | W=b'01 | Bitmap | W=b'10 | Bitmap | W=b'11 | Bitmap | b'0-pad |
   + ------ + ------ + ----- + ------ + ------ + ------ + ------ + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 2 bits | 7 bits | 2 bits | 7 bits | 24 bits |
        Figure 7: SCHC Compound ACK format with losses in windows 1 and 3 

```


```text
    
   |---- SCHC ACK Header ----|-W=b'00-|---- W=b'01 -----|---- W=b'10 -----|
   + ----------------------- + ------ + ------ + ------ + ------ + ------ + ------- +
   | RuleID | W=b'00 | C=b'0 | Bitmap | W=b'01 | Bitmap | W=b'10 | Bitmap | b'0-pad |
   + ------ + ------ + ----- + ------ + ------ + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 2 bits | 7 bits | 33 bits |
        Figure 8: SCHC Compound ACK format with losses in windows 0, 1 and 2 
```

#### SCHC Sender-Abort Messages

```text
    
   |---- Sender-Abort Header ----|
   + --------------------------- + ------- +
   | RuleID |   W    | FCN=ALL-1 | b'0-pad |
   + ------ + ------ + --------- + ------- +
   | 3 bits | 2 bits |  3 bits   | 88 bits |

        Figure 9: SCHC Sender-Abort Message

```

```text
    
   |---- Sender-Abort Header ----|
   + --------------------------- +
   | RuleID |   W    | FCN=ALL-1 |
   + ------ + ------ + --------- +
   | 3 bits | 2 bits |  3 bits   |

        Figure 9.1: SCHC Sender-Abort Message with no padding

```

#### SCHC Receiver-Abort Message

```text
    
   |- Receiver-Abort Header -|
   + ----------------------- + ------- +
   | RuleID | W=b'11 | C=b'1 | b'1-pad |
   + ------ + ------ + ----- + ------- +
   | 3 bits | 2 bits | 1 bit | 58 bits |
        Figure 10: SCHC Receiver-Abort format.
```




## Uplink ACK-on-Error Mode: Two-byte SCHC Header

### SCHC Fragment Formats


#### Regular SCHC Frgment
Figure 11 shows an example of a regular SCHC fragment for all fragments except the last one.
The penultimate tile of a SCHC Packet is of the regular size.

```text
    
   |-- SCHC Fragment Header --|
   + ------------------------ + ------- +
   | RuleID |   W    | FCN    | Payload |
   + ------ + ------ + ------ + ------- +
   | 8 bits | 3 bits | 5 bits | 80 bits |
        Figure 11: Regular SCHC Fragment format for all fragments except the last one

```

The SCHC ACK REQ is not used, instead the All-1 SCHC Fragment MUST be used. 
As per RFC8724, the All-0 message is distinguishable from the SCHC ACK REQ (All-1 message)

#### All-1 SCHC Fragment

Figure 12 shows an example of the All-1 message. 
The All-1 message MUST contain the last tile of the SCHC Packet.

```text
    
   |---  SCHC Fragment Header ---|
   + --------------------------- + ------------ +
   | RuleID |   W    | FCN=ALL-1 |    Payload   |
   + ------ + ------ + --------- + ------------ +
   | 8 bits | 3 bits |  5 bits   | 8 to 80 bits |

        Figure 12: All-1 SCHC Message with last tile

```

As per RFC8724 the All-1 must be distinguishable from the a SCHC Sender-Abort message (with same Rule ID, M and N values).
The All-1 MUST have the last tile of the SCHC Packet, that MUST be of at least 1 byte. 
The SCHC Sender-Abort message header size is of 1 byte, with no padding bits.

***Review how the message are distinguishable***
For the All-1 message to be distinguishable from the Sender-Abort message, the Sender-Abort message MUST be of 2 byte (only header with no padding).
This way, the minimum size of the All-1 is 3 bytes, and the Sender-Abort message is of 2 bytes.

#### SCHC ACK Format


```text
    
   |----- SCHC ACK Header ----|
   + ------------------------ + ------- +
   | RuleID | W=b'000 | C=b'1 | b'0-pad |
   + ------ + ------ + ----- + ------- +
   | 8 bits |  3 bits | 1 bit | 52 bits |
        Figure 13: SCHC Success ACK format.  
```



The SCHC Compound ACK message MUST be used for ACK failure messages.
The SCHC Compound ACK message is shown in Figure 14.
The SCHC Compound ACK can report up to 3 windows with losses.
W and bitmap groups MUST be ordered from the lowest-numbered window number to the highest-numbered window.
If window numbered 000 is present in the SCHC Compound ACK, the window number 000 MUST be placed between the Rule ID and C bit to avoid confusion with padding bits.
The SCHC Compound ACK MUST be 0 padded (Padding bits must be 0).


```text
    
   |----- SCHC ACK Header ----|-W=b'000-|----- W=b'001 -----|
   + ------------------------ + ------- + ------- + ------- + ------- +
   | RuleID | W=b'000 | C=b'0 |  Bitmap | W=b'001 |  Bitmap | b'0-pad |
   + ------ + ------- + ----- + ------- + ------- + ------- + ------- +
   | 8 bits |  3 bits | 1 bit | 15 bits |  3 bits | 15 bits | 19 bits |
        Figure 14: SCHC Compound ACK format. 
        On top are noted the window of each window number and bitmap group. 
        Losses are found in windows 0 and 1. 
```

```text
    
   |----- SCHC ACK Header ----|-W=b'001-|----- W=b'011 -----|
   + ------------------------ + ------- + ------- + ------- + ------- +
   | RuleID | W=b'001 | C=b'0 |  Bitmap | W=b'011 |  Bitmap | b'0-pad |
   + ------ + ------- + ----- + ------- + ------- + ------- + ------- +
   | 8 bits |  3 bits | 1 bit | 15 bits |  3 bits | 15 bits | 19 bits |
        Figure 15: SCHC Compound ACK format. 
        On top are noted the window of each window number and bitmap group. 
        Losses are found in windows 1 and 3. 
```


```text
    
   |----- SCHC ACK Header ----|-W=b'001-|----- W=b'011 -----|----- W=b'111 -----|
   + ------------------------ + ------- + ------- + ------- + ------- + ------- + ------- +
   | RuleID | W=b'001 | C=b'0 |  Bitmap | W=b'011 |  Bitmap | W=b'111 |  Bitmap | b'0-pad |
   + ------ + ------- + ----- + ------- + ------- + ------- + ------- + ------- + ------- +
   | 8 bits |  3 bits | 1 bit | 15 bits |  3 bits | 15 bits |  3 bits | 15 bits |  1 bit  |
        Figure 15: SCHC Compound ACK format. 
        On top are noted the window of each window number and bitmap group. 
        Losses are found in windows 1, 3 and 7. 
```



#### SCHC Sender-Abort Messages

```text
    
   |---- Sender-Abort Header ----|
   + --------------------------- + ------- +
   | RuleID |   W    | FCN=ALL-1 | b'0-pad |
   + ------ + ------ + --------- + ------- +
   | 8 bits | 3 bits |  5 bits   | 80 bits |

        Figure 16: SCHC Sender-Abort Message

```
```text
    
   |---- Sender-Abort Header ----|
   + --------------------------- + 
   | RuleID |   W    | FCN=ALL-1 |
   + ------ + ------ + --------- +
   | 8 bits | 3 bits |  5 bits   |

        Figure 16.1: SCHC Sender-Abort Message with no padding

```

#### SCHC Receiver-Abort Message

```text
    
   |-- Receiver-Abort Header -|
   + ------------------------ + ------- +
   | RuleID | W=b'111 | C=b'1 | b'1-pad |
   + ------ + ------- + ----- + ------- +
   | 8 bits |  3 bits | 1 bit | 58 bits |
        Figure 17: SCHC Receiver-Abort format.
```
