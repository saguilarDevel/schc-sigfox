
# SCHC-over-Sigfox F/R Message Formats
This section defines the SCHC fragment formats, the compound SCHC ACK format and the SCHC Abort formats.

## Uplink ACK-on-Error Mode: Single-byte SCHC Header

### SCHC Fragment Formats


#### Regular SCHC Frgment
Figure 1 shows an example of a regular SCHC fragment for all fragments except the last one.


```text
    
   |-- SCHC Fragment Header --|
   + ------------------------ + ------- +
   | RuleID |   W    | FCN    | Payload |
   + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 3 bits | 88 bits |
        Figure 1: Regular SCHC Fragment format for all fragments except the last one

```

The SCHC ACK REQ is not used, instead the All-1 SCHC Fragment MUST be used. 
As per RFC8724, the All-0 message is distinguishable from the SCHC ACK REQ (All-1 message)

#### All-1 SCHC Fragment

Figure 2 shows an example of the All-1 message. 
The All-1 message MUST contain the last tile of the SCHC Packet.

```text
    
   |---  SCHC Fragment Header ---|
   + --------------------------- + ------------ + ------------ +
   | RuleID |   W    | FCN=ALL-1 |    Payload   |     0-pad    |
   + ------ + ------ + --------- + ------------ + ------------ +
   | 3 bits | 2 bits |  3 bits   | 8 to 88 bits | 80 to 0 bits |

        Figure 2: All-1 SCHC Message with last tile

```

As per RFC8724 the All-1 must be distinguishable from the a SCHC Sender-Abort message (with same Rule ID, M and N values). 
The All-1 MUST have the last tile of the SCHC Packet, therefore there is a different. 
What happens with a payload of zeros (0) or ones (1) in All-1?


***Review how the message are distinguishable***


#### SCHC Compound ACK Format

Figure 3 shows the SCHC ACK format when all fragments have been correctly received (C=1).
```text
    
   |---- SCHC ACK Header ----|
   + ----------------------- + ------- +
   | RuleID |  W=00  |  C=1  |  0-pad  |
   + ------ + ------ + ----- + ------- +
   | 3 bits | 2 bits | 1 bit | 58 bits |
        Figure 3: SCHC Compound ACK format. On top are noted the window of each window number and bitmap group. Losses are found in windows 0 and 1. 
```

In case SCHC fragment losses are found in any windows (C=0), the SCHC Compound ACK MUST be used.
The SCHC Compound ACK message is shown in Figure 4.

The SCHC Compound ACK message MUST be used for ACK failure messages.
The Compound ACK:
* MUST only report windows with fragments losses.
* MUST include the window number of each bitmap.
* MUST report at least one window (the format will the same as RFC8724).
* MAY not report all windows of a SCHC Packet.
* Has a variable size.
* Compatible with SCHC Receiver Abort and ACK Failure format 

W and bitmap groups must be ordered from the lowest-numbered window number to the highest-numbered window.
If window numbered 00 is present in the compound ACK, the window MUST be placed between the Rule ID and C bit to avoid confusion with padding bits.
The Compound ACK MUST be 0 padded (Padding bits must be 0).


```text
    
   |---- SCHC ACK Header ----|- W=00 -|----- W=01 ------|
   + ----------------------- + ------ + ------ + ------ + ------- +
   | RuleID |  W=00  |  C=0  | Bitmap |  W=01  | Bitmap |  0-pad  |
   + ------ + ------ + ----- + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 42 bits |
        Figure 4: SCHC Compound ACK format. On top are noted the window of each window number and bitmap group. Losses are found in windows 0 and 1. 

```

Following figures are examples of the Compound ACK message format.

```text
    
   |---- SCHC ACK Header ----|- W=01 -|----- W=11 ------|
   + ----------------------- + ------ + ------ + ------ + ------- +
   | RuleID |  W=01  |  C=0  | Bitmap |  W=11  | Bitmap |  0-pad  |
   + ------ + ------ + ----- + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 42 bits |
        Figure 5: SCHC Compound ACK format with losses in windows 1 and 3 

```

```text
    
   |---- SCHC ACK Header ----|- W=00 -|----- W=10 ------|
   + ----------------------- + ------ + ------ + ------ + ------- +
   | RuleID |  W=00  |  C=0  | Bitmap |  W=10  | Bitmap |  0-pad  |
   + ------ + ------ + ----- + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 42 bits |
        Figure 6: SCHC Compound ACK format with losses in windows 1 and 3 

```

Figure 7 shows the Compound ACK message format when losses are found in all windows.
The window and bitmap groups are ordered from window numbered 00 to 11, notifying all four possible windows.

```text
    
   |---- SCHC ACK Header ----|- W=00 -|----- W=01 ------|----- W=10 ------|----- W=11 ------|
   + ----------------------- + ------ + ------ + ------ + ------ + ------ + ------ + ------ + ------- +
   | RuleID |  W=00  |  C=0  | Bitmap |  W=01  | Bitmap |  W=10  | Bitmap |  W=11  | Bitmap |  0-pad  |
   + ------ + ------ + ----- + ------ + ------ + ------ + ------ + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 2 bits | 7 bits | 2 bits | 7 bits | 24 bits |
        Figure 7: SCHC Compound ACK format with losses in windows 1 and 3 

```


```text
    
   |---- SCHC ACK Header ----|- W=00 -|----- W=01 ------|----- W=10 ------|
   + ----------------------- + ------ + ------ + ------ + ------ + ------ + ------- +
   | RuleID |  W=00  |  C=0  | Bitmap |  W=01  | Bitmap |  W=10  | Bitmap |  0-pad  |
   + ------ + ------ + ----- + ------ + ------ + ------ + ------ + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 2 bits | 7 bits | 33 bits |
        Figure 8: SCHC Compound ACK format with losses in windows 0, 1 and 2 
```

#### SCHC Sender-Abort Messages

```text
    
   |---- Sender-Abort Header ----|
   + --------------------------- + ------- +
   | RuleID |   W    | FCN=ALL-1 |  0-pad  |
   + ------ + ------ + --------- + ------- +
   | 3 bits | 2 bits |  3 bits   | 88 bits |

        Figure 9: SCHC Sender-Abort Message

```

#### SCHC Receiver-Abort Message

```text
    
   |- Receiver-Abort Header -|
   + ----------------------- + ------- +
   | RuleID |  W=11  |  C=1  |  1-pad  |
   + ------ + ------ + ----- + ------- +
   | 3 bits | 2 bits | 1 bit | 58 bits |
        Figure 10: SCHC Sender-Abort format.
```




## Uplink ACK-on-Error Mode: Two-byte SCHC Header

### SCHC Fragment Formats


#### Regular SCHC Frgment
Figure 11 shows an example of a regular SCHC fragment for all fragments except the last one.


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

***Review how the message are distinguishable***


#### SCHC Compound ACK Format

The SCHC Compound ACK message is shown in Figure 13.
The Compound ACK can report up to 2 windows with losses.



```text
    
   |---- SCHC ACK Header ----|- W=000 -|----- W=001 ------|
   + ----------------------- + ------- + ------ + ------- + ------- +
   | RuleID | W=000  |  C=0  |  Bitmap | W=001  |  Bitmap |  0-pad  |
   + ------ + ------ + ----- + ------- + ------ + ------- + ------- +
   | 8 bits | 3 bits | 1 bit | 15 bits | 3 bits | 15 bits |
        Figure 13: SCHC Compound ACK format. On top are noted the window of each window number and bitmap group. Losses are found in windows 0 and 1. 
```

```text
    
   |---- SCHC ACK Header ----|- W=001 -|----- W=011 ------|
   + ----------------------- + ------- + ------ + ------- + ------- +
   | RuleID | W=001  |  C=0  |  Bitmap | W=011  |  Bitmap |  0-pad  |
   + ------ + ------ + ----- + ------- + ------ + ------- + ------- +
   | 8 bits | 3 bits | 1 bit | 15 bits | 3 bits | 15 bits |
        Figure 14: SCHC Compound ACK format. On top are noted the window of each window number and bitmap group. Losses are found in windows 1 and 3. 
```



#### SCHC Sender-Abort Messages

```text
    
   |---- Sender-Abort Header ----|
   + --------------------------- + ------- +
   | RuleID |   W    | FCN=ALL-1 |  0-pad  |
   + ------ + ------ + --------- + ------- +
   | 8 bits | 3 bits |  5 bits   | 80 bits |

        Figure 9: SCHC Sender-Abort Message

```

#### SCHC Receiver-Abort Message

```text
    
   |- Receiver-Abort Header -|
   + ----------------------- + ------- +
   | RuleID |  W=111 |  C=1  |  1-pad  |
   + ------ + ------ + ----- + ------- +
   | 8 bits | 3 bits | 1 bit | 58 bits |
        Figure 9: SCHC Sender-Abort format.
```
