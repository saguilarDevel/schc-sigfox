# New fragment formats for SCHC over Sigfox

## Single-byte SCHC Header for Uplink Fragmentation

### Uplink No-ACK Mode: Single-byte SCHC Header

Single-byte SCHC Header No-ACK mode is RECOMMENDED to be used for transmitting short, non-critical packets that require fragmentation and do not require full reliability. This mode can be used by uplink-only devices that do not support downlink communications, or by bidirectional devices when
   they send non-critical data. 

The RECOMMENDED Fragmentation Header size is 8 bits, and it is
   composed as follows:

   * RuleID size: 3 bits
   * DTag size (T): 0 bits
   * Fragment Compressed Number (FCN) size (N): 5 bits
   * As per [RFC8724], in the No-ACK mode the W (window) field is not
      present.
   * RCS size: 5 bits (Not used)

The maximum SCHC Packet size is of 340 bytes.

### Uplink ACK-on-Error Mode: Single-byte SCHC Header

ACK-on-Error with single-byte header is RECOMMENDED for medium to large size packets that need to be sent reliably.  ACK-on-Error is optimal for Sigfox transmissions, since it leads to a reduced number of ACKs in the lower capacity downlink channel.  Also, downlink messages can be sent asynchronously and opportunistically.

Allowing transmission of packets/files up to 300 bytes long, the SCHC uplink Fragmentation Header size is RECOMMENDED to be 8 bits in size and is composed as follows:

   * Rule ID size: 3 bits
   * DTag size (T): 0 bits
   * Window index (W) size (M): 2 bits
   * Fragment Compressed Number (FCN) size (N): 3 bits
   * MAX_ACK_REQUESTS: 5
   * WINDOW_SIZE: 7 (with a maximum value of FCN=0b110)
   * Tile size: 11 bytes
   * Retransmission Timer: Application-dependent
   * Inactivity Timer: Application-dependent
   * RCS size: 3 bits

## Two-byte SCHC Header for Uplink Fragmentation

### Uplink ACK-on-Error Mode: Two-byte SCHC Header Option 1

ACK-on-Error with two-byte header is RECOMMENDED for very large size packets that need to be sent reliably.  ACK-on-Error is optimal for Sigfox transmissions, since it leads to a reduced number of ACKs in the lower capacity downlink channel.  Also, downlink messages can be sent asynchronously and opportunistically.

In order to allow transmission of large packets/files up to 480 bytes long, the SCHC uplink Fragmentation Header size is RECOMMENDED to be 16 bits in size and composed as follows:

   *  Rule ID size is: 6 bits
   *  DTag size (T) is: 0 bits
   *  Window index (W) size (M): 2 bits
   *  Fragment Compressed Number (FCN) size (N): 4 bits.
   *  MAX_ACK_REQUESTS: 5
   *  WINDOW_SIZE: 12 (with a maximum value of FCN=0b1011)
   *  Tile size: 10 bytes
   *  Retransmission Timer: Application-dependent
   *  Inactivity Timer: Application-dependent
   *  RCS size: 4 bits



### Uplink ACK-on-Error Mode: Two-byte SCHC Header Option 2

In order to allow transmission of very large packets/files up to 2250 bytes long, the SCHC uplink Fragmentation Header size is RECOMMENDED to be 16 bits in size and composed as follows:

   * Rule ID size is: 8 bits
   * DTag size (T) is: 0 bits
   * Window index (W) size (M): 3 bits
   * Fragment Compressed Number (FCN) size (N): 5 bits.
   * MAX_ACK_REQUESTS: 5
   * WINDOW_SIZE: 31 (with a maximum value of FCN=0b11110)
   * Tile size: 10 bytes
   * Retransmission Timer: Application-dependent
   * Inactivity Timer: Application-dependent
   * RCS size: 5 bits



## SCHC-over-Sigfox F/R Message Formats

This section depicts the different formats of SCHC Fragment, SCHC ACK (including the SCHC Compound ACK defined in [I-D.ietf-lpwan-schc-compound-ack]), and SCHC Abort used in SCHC over Sigfox.

### Uplink No-ACK Mode: Single-byte SCHC Header
#### Regular SCHC Fragment
Figure A shows an example of a regular SCHC fragment for all
   fragments except the last one.  As tiles are of 11 bytes, padding
   MUST NOT be added.
```text
                |- SCHC Fragment Header -|
                + ---------------------- + ------- +
                |   RuleID   |    FCN    | Payload |
                + ---------- + --------- + ------- +
                |   3 bits   |  5 bits   | 88 bits |

      Figure A: Regular SCHC Fragment format for all fragments except
                                the last one
```

####  All-1 SCHC Fragment
Figure B shows an example of the All-1 message.  The All-1 message
   MUST contain the last tile of the SCHC Packet.  The last tile MUST be
   of at least 1 byte (one L2 word).  Padding MUST NOT be added, as the
   resulting size is L2-word-multiple.

   The All-1 messages includes a 5-bit RCS, and 3 bits are added as padding to complete one byte. The payload size of the All-1 message ranges from 8 to 80 bits.
```text

              |--------  SCHC Fragment Header -------|
              + ------------------------------------ + ------------ +
              | RuleID | FCN=ALL-1 |  RCS   |   000  |   Payload    |
              + ------ + --------- + ------ + ------ + ------------ +
              | 3 bits |  5 bits   | 5 bits | 3 bits | 8 to 80 bits |

             Figure B: All-1 SCHC Message format with last tile

```
#### SCHC Sender-Abort Message format

```text
                      |- Sender-Abort Header -|
                      + --------------------- +
                      | RuleID |   FCN=ALL-1  |
                      + ------ + -- --------- +
                      | 3 bits |     5 bits   |

                Figure C: SCHC Sender-Abort message format

```

### Uplink ACK-on-Error Mode: Single-byte SCHC Header

#### Regular SCHC Fragment

   Figure 3 shows an example of a regular SCHC fragment for all
   fragments except the last one.  As tiles are of 11 bytes, padding
   MUST NOT be added.
```text
                |-- SCHC Fragment Header --|
                + ------------------------ + ------- +
                | RuleID |   W    | FCN    | Payload |
                + ------ + ------ + ------ + ------- +
                | 3 bits | 2 bits | 3 bits | 88 bits |

      Figure 3: Regular SCHC Fragment format for all fragments except
                                the last one
```

   The use of SCHC ACK REQ is NOT RECOMMENDED, instead the All-1 SCHC
   Fragment SHOULD be used to request a SCHC ACK from the receiver
   (Network SCHC).  As per [RFC8724], the All-0 message is
   distinguishable from the SCHC ACK REQ (All-1 message).  The
   penultimate tile of a SCHC Packet is of regular size.

####  All-1 SCHC Fragment

   Figure 4 shows an example of the All-1 message.  The All-1 message
   MUST contain the last tile of the SCHC Packet.  The last tile MUST be
   of at least 1 byte (one L2 word).  Padding MUST NOT be added, as the
   resulting size is L2-word-multiple.

   The All-1 messages includes a 3-bit RCS, and 5 bits are added as padding to complete one byte. The payload size of the All-1 message ranges from 8 to 80 bits.
```text

              |-------------  SCHC Fragment Header -----------|
              + --------------------------------------------- + ------------ +
              | RuleID |   W    | FCN=ALL-1 |  RCS   |  00000 |   Payload    |
              + ------ + ------ + --------- + ------ + ------ + ------------ +
              | 3 bits | 2 bits |  3 bits   | 3 bits | 5 bits | 8 to 80 bits |

             Figure 4: All-1 SCHC Message format with last tile

```
   As per [RFC8724] the All-1 must be distinguishable from a SCHC
   Sender-Abort message (with same Rule ID, M, and N values).  The All-1
   MUST have the last tile of the SCHC Packet, which MUST be of at least
   1 byte.  The SCHC Sender-Abort message header size is of 1 byte, with
   no padding bits.

   For the All-1 message to be distinguishable from the SCHC Sender-Abort
   message, the Sender-Abort message MUST be of 1 byte (only header with
   no padding).  This way, the minimum size of the All-1 is 3 bytes, and
   the Sender-Abort message is 1 byte.

#### SCHC ACK Format

   Figure 5 shows the SCHC ACK format when all fragments have been
   correctly received (C=1).  Padding MUST be added to complete the
   64-bit Sigfox downlink frame payload size.
   ```text
                  |---- SCHC ACK Header ----|
                  + ----------------------- + ------- +
                  | RuleID |    W   | C=b'1 | b'0-pad |
                  + ------ + ------ + ----- + ------- +
                  | 3 bits | 2 bits | 1 bit | 58 bits |

                 Figure 5: SCHC Success ACK message format
```
                  

   In case SCHC fragment losses are found in any of the windows of the
   SCHC Packet (C=0), the SCHC Compound ACK defined in
   [I-D.ietf-lpwan-schc-compound-ack] MUST be used.  The SCHC Compound
   ACK message format is shown in Figure 6.  
   
REMOVE-->The window numbered 00, if present in the SCHC Compound ACK, MUST be placed between the Rule ID
   and the C bit to avoid confusion with padding bits.  As padding is
   needed for the SCHC Compound ACK, padding bits MUST be 0 to make
   subsequent window numbers and bitmaps distinguishable.<-- REMOVE

```text
   |---- SCHC ACK Header ----|-W = x -|...| --- W = x + i ---|
   + ----------------------- + ------ +...+ ------- + ------ + ------- +
   | RuleID | W=b'x  | C=b'0 | Bitmap |...| W=b'x+i | Bitmap | b'0-pad |
   + ------ + ------ + ----- + ------ +...+ ------- + ------ + ------- +
   | 3 bits | 2 bits | 1 bit | 7 bits |   | 2 bits  | 7 bits |

      On top are noted the window number of the corresponding bitmap.
      Losses are found in windows x,...,x+i.

               Figure 6: SCHC Compound ACK message format
```
   The following figures show examples of the SCHC Compound ACK message
   format, when used on SCHC over Sigfox.
```text
      |---- SCHC ACK Header ----|- W=00 -|----- W=01 ------|
      + ----------------------- + ------ + ------ + ------ + ------- +
      | RuleID | W=b'00 | C=b'0 | Bitmap | W=b'01 | Bitmap | b'0-pad |
      + ------ + ------ + ----- + ------ + ------ + ------ + ------- +
      | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 42 bits |

           Losses are found in windows 00 and 01.

                   Figure 7: SCHC Compound ACK example 1
```
```text
      |---- SCHC ACK Header ----|- W=01 -|----- W=11 ------|
      + ----------------------- + ------ + ------ + ------ + ------- +
      | RuleID | W=b'01 | C=b'0 | Bitmap | W=b'11 | Bitmap | b'0-pad |
      + ------ + ------ + ----- + ------ + ------ + ------ + ------- +
      | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 42 bits |

           Losses are found in windows 01 and 11.

                   Figure 8: SCHC Compound ACK example 2
```
```text
      |---- SCHC ACK Header ----|- W=00 -|----- W=10 ------|
      + ----------------------- + ------ + ------ + ------ + ------- +
      | RuleID | W=b'00 | C=b'0 | Bitmap | W=b'10 | Bitmap | b'0-pad |
      + ------ + ------ + ----- + ------ + ------ + ------ + ------- +
      | 3 bits | 2 bits | 1 bit | 7 bits | 2 bits | 7 bits | 42 bits |

           Losses are found in windows 00 and 10.

                   Figure 9: SCHC Compound ACK example 3
```
   Figure 10 shows the SCHC Compound ACK message format when losses are
   found in all windows.  The window numbers and its corresponding
   bitmaps are ordered from window numbered 00 to 11, notifying all four
   possible windows.
```text
     |- SCHC ACK Header -|W=b'00|-- W=b'01 ---|
     +-------------------+------+ ---- +------+
     |RuleID|W=b'00|C=b'0|Bitmap|W=b'01|Bitmap| ...
     +------+------+-----+------+------+------+
     |3 bits|2 bits|1 bit|7 bits|2 bits|7 bits|


                |--- W=b'10 --|--- W=b'11 --|
                |------+------+------+------+-------+
            ... |W=b'10|Bitmap|W=b'11|Bitmap|b'0-pad|
                |------+------+------+------+-------+
                |2 bits|7 bits|2 bits|7 bits|24 bits|

           Losses are found in windows 00, 01, 10 and 11.

                   Figure 10: SCHC Compound ACK example 4
```
```text
   |- SCHC ACK Header -|W=b'00|-- W=b'01 ---|--- W=b'10 --|
   +-------------------+------+------+------+------+------+-------+
   |RuleID|W=b'00|C=b'0|Bitmap|W=b'01|Bitmap|W=b'10|Bitmap|b'0-pad|
   +------+------+-----+------+------+------+------+------+-------+
   |3 bits|2 bits|1 bit|7 bits|2 bits|7 bits|2 bits|7 bits|33 bits|

           Losses are found in windows 00, 01 and 10.

                   Figure 11: SCHC Compound ACK example 5
```
#### SCHC Sender-Abort Message format

```text
                      |---- Sender-Abort Header ----|
                      + --------------------------- +
                      | RuleID | W=b'11 | FCN=ALL-1 |
                      + ------ + ------ + --------- +
                      | 3 bits | 2 bits |  3 bits   |

                Figure 12: SCHC Sender-Abort message format

```

####  SCHC Receiver-Abort Message format

```text
                   |- Receiver-Abort Header -|
                   + ----------------------- + ------- +
                   | RuleID | W=b'11 | C=b'1 | b'1-pad |
                   + ------ + ------ + ----- + ------- +
                   | 3 bits | 2 bits | 1 bit | 58 bits |

               Figure 13: SCHC Receiver-Abort message format
```



### Uplink ACK-on-Error Mode: Two-byte SCHC Header Option 1

#### Regular SCHC Fragment

   Figure 14 shows an example of a regular SCHC fragment for all
   fragments except the last one, while using Option 1.  
   The penultimate tile of a SCHC Packet is of the regular size.

   The SCHC Fragment Header is 0-padded with 4 bits to complete the two-byte size.  
   ```text
                      |------- SCHC Fragment Header ------|
                      + --------------------------------- + ------- +
                      | RuleID |    W   |  FCN   |  0000  | Payload |
                      + ------ + ------ + ------ + ------ + ------- +
                      | 6 bits | 2 bits | 4 bits | 4 bits | 80 bits |
   
         Figure 14: Regular SCHC Fragment format for all fragments except
                                   the last one
```

The use of SCHC ACK REQ is NOT RECOMMENDED, instead the All-1 SCHC
   Fragment SHOULD be used to request a SCHC ACK from the receiver
   (Network SCHC).  As per [RFC8724], the All-0 message is
   distinguishable from the SCHC ACK REQ (All-1 message).

#### All-1 SCHC Fragment

   Figure 15 shows an example of the All-1 message, for Option 1.  
   The All-1 message MUST contain the last tile of the SCHC Packet.

   The All-1 message contains a RCS of 4 bits to complete the two-byte size.
   The size of the last tile ranges from 8 to 80 bits.
   ```text
                 |--------- SCHC Fragment Header -------|
                 + ------------------------------------ + ------------ +
                 | RuleID |    W   | FCN=ALL-1 |  RCS   |    Payload   |
                 + ------ + ------ + --------- + ------ + ------------ +
                 | 6 bits | 2 bits |  4 bits   | 4 bits | 8 to 80 bits |

            Figure 15: All-1 SCHC message format with last tile
```

   As per [RFC8724] the All-1 must be distinguishable from the a SCHC
   Sender-Abort message (with same Rule ID, M and N values).  The All-1
   MUST have the last tile of the SCHC Packet, that MUST be of at least
   1 byte.  The SCHC Sender-Abort message header size is of 2 byte, with
   no padding bits.

   For the All-1 message to be distinguishable from the Sender-Abort
   message, the Sender-Abort message MUST be of 2 byte (only header with
   no padding).  This way, the minimum size of the All-1 is 3 bytes, and
   the Sender-Abort message is 2 bytes.

#### SCHC ACK Format

   Figure 16 shows the SCHC ACK format when all fragments have been
   correctly received (C=1).  Padding MUST be added to complete the
   64-bit Sigfox downlink frame payload size.
```text
                    |----- SCHC ACK Header ----|
                    + ------------------------ + ------ +
                    | RuleID |    W   | C=b'1 | b'0-pad |
                    + ------ + ------ + ----- + ------- +
                    | 6 bits | 2 bits | 1 bit | 55 bits |

                 Figure 16: SCHC Success ACK message format
```

   The SCHC Compound ACK message MUST be used in case SCHC fragment
   losses are found in any window of the SCHC Packet (C=0).  The SCHC
   Compound ACK message format is shown in Figure 17.  The SCHC Compound
   ACK can report up to 3 windows with losses.  
   REMOVE--> The window number (W)
   and its corresponding bitmap MUST be ordered from the lowest-numbered 
   window number to the highest-numbered window.  If window numbered 000
   is present in the SCHC Compound ACK, the window number 000 MUST be
   placed between the Rule ID and C bit to avoid confusion with padding
   bits.

   When sent in the downlink, the SCHC Compound ACK MUST be 0 padded
   (Padding bits must be 0) to complement the 64 bits required by the
   Sigfox payload.

```text
     |- SCHC ACK Header -| W=b'w1 |...|--- W=b'wi ---|
     +-------------------+-------+...+-------+-------+-------+
     |RuleID|W=b'w1|C=b'0|Bitmap |...|W=b'wi |Bitmap |b'0-pad|
     +------+------+-----+-------+...|-------+-------+-------+
     |6 bits|2 bits|1 bit|15 bits|   | 2 bits|15 bits|

           On top are noted the window number
                   of the corresponding bitmap.
           Losses are found in windows w,...,wi.

                Figure 17: SCHC Compound ACK message format
```

#### SCHC Sender-Abort Messages
```text
                   |---- Sender-Abort Header ----|
                   + --------------------------- +
                   | RuleID | W=b'11 | FCN=ALL-1 |
                   + ------ + ------ + --------- +
                   | 6 bits | 2 bits |  5 bits   |

                Figure 18: SCHC Sender-Abort message format
```
#### SCHC Receiver-Abort Message
```text
                 |- Receiver-Abort Header -|
                 + ----------------------- + ------- +
                 | RuleID | W=b'11 | C=b'1 | b'1-pad |
                 + ------ + ------ + ----- + ------- +
                 | 6 bits | 2 bits | 1 bit | 55 bits |

               Figure 19: SCHC Receiver-Abort message format
```



### Uplink ACK-on-Error Mode: Two-byte SCHC Header Option 2

#### Regular SCHC Fragment

   Figure 20 shows an example of a regular SCHC fragment for all
   fragments except the last one, while using Option 2.  
   The penultimate tile of a SCHC Packet
   is of the regular size.

   ```text
                      |------- SCHC Fragment Header -------|
                      + ----------------------- + -------- +
                      | RuleID |    W   |  FCN   | Payload |
                      + ------ + ------ + ------ + ------- +
                      | 8 bits | 3 bits | 5 bits | 80 bits |
   
         Figure 20: Regular SCHC Fragment format for all fragments except
                                   the last one
```

The use of SCHC ACK REQ is NOT RECOMMENDED, instead the All-1 SCHC
   Fragment SHOULD be used to request a SCHC ACK from the receiver
   (Network SCHC).  As per [RFC8724], the All-0 message is
   distinguishable from the SCHC ACK REQ (All-1 message).

#### All-1 SCHC Fragment

   Figure 21 shows an example of the All-1 message.  The All-1 message
   MAY contain the last tile of the SCHC Packet.

   The All-1 message SCHC Fragment Header contains an RCS of 5 bits, and 3 padding bits to complete 3 bytes. 
   The size of the last tile ranges from 8 to 72 bits.
   ```text
            |-------------- SCHC Fragment Header -----------|
            + --------------------------------------------- + ------------ +
            | RuleID |    W   | FCN=ALL-1 |  RCS   |  000   |    Payload   |
            + ------ + ------ + --------- + ------ + ------ + ------------ +
            | 8 bits | 3 bits |  5 bits   | 5 bits | 3 bits | 8 to 72 bits |

            Figure 21: All-1 SCHC message format with last tile
```
   As per [RFC8724] the All-1 must be distinguishable from the a SCHC
   Sender-Abort message (with same Rule ID, M and N values).  The All-1
   MUST have the last tile of the SCHC Packet, that MUST be of at least
   1 byte.  The SCHC Sender-Abort message header size is of 2 byte, with
   no padding bits.

   For the All-1 message to be distinguishable from the Sender-Abort
   message, the Sender-Abort message MUST be of 2 byte (only header with
   no padding).  This way, the minimum size of the All-1 is 3 bytes (without any tile), and the Sender-Abort message is 2 bytes.

#### SCHC ACK Format

   Figure 22 shows the SCHC ACK format when all fragments have been
   correctly received (C=1).  Padding MUST be added to complete the
   64-bit Sigfox downlink frame payload size.
```text
                    |----- SCHC ACK Header ----|
                    + ------------------------ + ------ +
                    | RuleID |    W   | C=b'1 | b'0-pad |
                    + ------ + ------ + ----- + ------- +
                    | 8 bits | 3 bits | 1 bit | 52 bits |

                 Figure 22: SCHC Success ACK message format
```

   The SCHC Compound ACK message MUST be used in case SCHC fragment
   losses are found in any window of the SCHC Packet (C=0).  The SCHC
   Compound ACK message format is shown in Figure 23.  The SCHC Compound
   ACK can report up to 3 windows with losses.  
   REMOVE--> The window number (W)
   and its corresponding bitmap MUST be ordered from the lowest-numbered 
   window number to the highest-numbered window.  If window numbered 000
   is present in the SCHC Compound ACK, the window number 000 MUST be
   placed between the Rule ID and C bit to avoid confusion with padding
   bits.

   When sent in the downlink, the SCHC Compound ACK MUST be 0 padded
   (Padding bits must be 0) to complement the 64 bits required by the
   Sigfox payload.

```text
     |- SCHC ACK Header -| W=b'w1 |...|--- W=b'wi ---|
     +-------------------+-------+...+-------+-------+-------+
     |RuleID|W=b'w1|C=b'0|Bitmap |...|W=b'wi |Bitmap |b'0-pad|
     +------+------+-----+-------+...|-------+-------+-------+
     |8 bits|3 bits|1 bit|31 bits|   | 3 bits|31 bits|

           On top are noted the window number
                   of the corresponding bitmap.
           Losses are found in windows w,...,wi.

                Figure 23: SCHC Compound ACK message format
```

#### SCHC Sender-Abort Messages
```text
                   |---- Sender-Abort Header ----|
                   + ---------------------------- +
                   | RuleID | W=b'111 | FCN=ALL-1 |
                   + ------ + ------- + --------- +
                   | 8 bits |  3 bits |  5 bits   |

                Figure 24: SCHC Sender-Abort message format
```
#### SCHC Receiver-Abort Message
```text
                 |- Receiver-Abort Header -|
                 + ----------------------- + ------- +
                 | RuleID | W=b'11 | C=b'1 | b'1-pad |
                 + ------ + ------ + ----- + ------- +
                 | 8 bits | 3 bits | 1 bit | 52 bits |

               Figure 25: SCHC Receiver-Abort message format
```



