# Fragmentation examples 

In this document are presented details about the SCHC-over-Sigfox implementation
using the LoPy, Sigfox Backend and Google Cloud.

## SCHC-over-Sigfox implementation


### Sigfox Sequence Number

The Sigfox Sequence Number (Seq) represented is only available at the receiver, 
and it shows whether there are missing fragments between the All-1 and the penultimate 
SCHC fragment.
This because is not possible for the receiver to know (without a RCS), 
if there are missing fragment
between the last received SCHC fragment and the All-1.

### No-ACK Mode
#### Uplink No-ACK Mode

The FCN field indicates the size of the data packet. 
The first fragment is marked with FCN = X-1, where X is the number of fragments the message is splitted.
All fragments are marked with decreasing FCN values.
Last packet fragment is marked with the FCN = All-1 (1111).
#### Case No losses

All fragments are send and received successfully.
```text
        Sender                              Receiver
          |-------FCN=6 (0110), Seq=1-------->|
          |-------FCN=5 (0101), Seq=2-------->|
          |-------FCN=4 (0100), Seq=3-------->|
          |-------FCN=3 (0011), Seq=4-------->|
          |-------FCN=2 (0010), Seq=5-------->|
          |-------FCN=1 (0001), Seq=6-------->|
          |-------FCN=15 (1111), Seq=7------->| All fragments received
        (End)
```
When the first SCHC fragment is received, the Receiver can calculate the 
total number of SCHC fragments that composed the SCHC Packet.
For example, if the first fragment is numbered with FCN=6, the receiver can 
expect 6 messages more (with FCN going from 5 downward, and the last with a
FCN equal to 15).

#### Case losses on any fragment except the first.



```text
        Sender                      Receiver
          |-------FCN=6, Seq=1-------->|
          |-------FCN=5, Seq=2----X--->|
          |-------FCN=4, Seq=3-------->|
          |-------FCN=3, Seq=4-------->|
          |-------FCN=2, Seq=5-------->|
          |-------FCN=1, Seq=6-------->|
          |-------FCN=15, Seq=7------->| Missing Fragment
        (End)
```
#### Case The first fragment is lost

If some fragments are lost before the first SCHC fragment arrives, the Receiver
may not be able to know. One solution is by using the Sequence number. 
However, it may not be possible
to know, as other control messages (with their sequence number) may have been
send.

```text
        Sender                      Receiver
          |-------FCN=6, Seq=1----X--->|
          |-------FCN=5, Seq=2-------->|
          |-------FCN=4, Seq=3-------->|
          |-------FCN=3, Seq=4-------->|
          |-------FCN=2, Seq=5-------->|
          |-------FCN=1, Seq=6-------->|
          |-------FCN=15, Seq=7------->| Missing Fragment
        (End)
```

One solution is to used the same logic as in ACK-on-Error, in which the fragments are
numbered from Window_size - 1 downwards. 

```text
        Sender                      Receiver
          |-------FCN=14, Seq=1----X-->|
          |-------FCN=13, Seq=2------->|
          |-------FCN=12, Seq=3------->|
          |-------FCN=11, Seq=4------->|
          |-------FCN=10, Seq=5------->|
          |-------FCN=9,  Seq=6------->|
          |-------FCN=15, Seq=7------->| Missing Fragment
        (End)
```

This way the Receiver is able to know if all fragments have been received or not.
Other option may be to include a Reassamble Check Sequence (RCS) as proposed in SCHC.

```text
        Sender                      Receiver
          |-------FCN=6, Seq=1----X--->|
          |-------FCN=5, Seq=2-------->|
          |-------FCN=4, Seq=3-------->|
          |-------FCN=3, Seq=4-------->|
          |-------FCN=2, Seq=5-------->|
          |-------FCN=1, Seq=6-------->|
          |----FCN=15 + RCS, Seq=7---->| Integrity check: failure
        (End)
```


### Uplink ACK-on-Error Mode: Single-byte SCHC Header

The single-byte SCHC header ACK-on-Error mode allows packet sizes up to
300 bytes. The SCHC fragments may be delivered asynchronously and opportunistically. 

#### Case No losses

The downlink must be enable in the sender to allow a message from the receiver. 
The DL Enable in the figures shows where the sender should enable the downlink, and 
wait for an ACK.

```text
        Sender                      Receiver
          |-----W=0, FCN=6, Seq=1----->|
          |-----W=0, FCN=5, Seq=2----->|
          |-----W=0, FCN=4, Seq=3----->|
          |-----W=0, FCN=3, Seq=4----->|
          |-----W=0, FCN=2, Seq=5----->|
          |-----W=0, FCN=1, Seq=6----->|
DL Enable |-----W=0, FCN=0, Seq=7----->|
      (no ACK)
          |-----W=1, FCN=6, Seq=8----->|
          |-----W=1, FCN=5, Seq=9----->|
          |-----W=1, FCN=4, Seq=10---->|
DL Enable |-----W=1, FCN=7, Seq=11---->| All fragments received
          |<------ ACK, W=1, C=1 ------| C=1
        (End)
```

In the LoPy, if an ACK is not received, the socket performs a timeout with an error 
number 115 [Errno 115] ENETDOWN.

#### Case Fragments lost in first window:

In this case, fragments are lost in the first window (W=0). 
After the first All-0 message arrives, the Receiver
leverage the opportunity and sends an ACK with the corresponding bitmap and C=0.

After the missing fragment from the first window (W=0) are resend, the sender without
opening a reception window, continues to the following window.
The All-1 fragment is send, the downlink is enable and the ACK received with a C=1.

```text
        Sender                      Receiver
          |-----W=0, FCN=6, Seq=1----->|
          |-----W=0, FCN=5, Seq=2--X-->|
          |-----W=0, FCN=4, Seq=3----->|
          |-----W=0, FCN=3, Seq=4----->|
          |-----W=0, FCN=2, Seq=5--X-->|
          |-----W=0, FCN=1, Seq=6----->|
DL Enable |-----W=0, FCN=0, Seq=7----->| Missing Fragments W=0 => FCN=5, Seq=2 and FCN=2, Seq=5
          |<------ ACK, W=0, C=0 ------| Bitmap:1011011
          |-----W=0, FCN=5, Seq=8----->|
          |-----W=0, FCN=2, Seq=9----->|
      (no ACK)
          |-----W=1, FCN=6, Seq=10---->|
          |-----W=1, FCN=5, Seq=11---->|
          |-----W=1, FCN=4, Seq=12---->|
DL Enable |-----W=1, FCN=7, Seq=13---->| All fragments received
          |<------ ACK, W=1, C=1 ------| C=1
        (End)
```




#### Case Fragments All-0 lost in first window (W=0):

The All-0 of the first window (W=0) is lost, therefore 
the Receiver waits for next All-X message to generate 
the corresponding ACK, notifying the absence of the All-0 of window 0.

The senders resends the missing All-0 messages (with any other missing 
fragment from window 0). Note that this behaviour can take place in any
intermeadiate window if the All-0 message is lost.

```text
        Sender                      Receiver
          |-----W=0, FCN=6, Seq=1----->|
          |-----W=0, FCN=5, Seq=2----->|
          |-----W=0, FCN=4, Seq=3----->|
          |-----W=0, FCN=3, Seq=4----->|
          |-----W=0, FCN=2, Seq=5----->|
          |-----W=0, FCN=1, Seq=6----->|
DL Enable |-----W=0, FCN=0, Seq=7--X-->|
      (no ACK)
          |-----W=1, FCN=6, Seq=8----->|
          |-----W=1, FCN=5, Seq=9----->|
          |-----W=1, FCN=4, Seq=10---->|
DL Enable |-----W=1, FCN=7, Seq=11---->| Missing Fragment W=0, FCN=0, Seq=7
          |<------ ACK, W=0, C=0 ------| Bitmap:1111110
DL Enable |-----W=0, FCN=0, Seq=12---->| All fragments received
          |<------ ACK, W=1, C=1 ------| C=1
        (End)
```

In this case, in the first window (W=0), besides the All-0,
there are others lost fragment.


```text
        Sender                      Receiver
          |-----W=0, FCN=6, Seq=1----->|
          |-----W=0, FCN=5, Seq=2--X-->|
          |-----W=0, FCN=4, Seq=3----->|
          |-----W=0, FCN=3, Seq=4--X-->|
          |-----W=0, FCN=2, Seq=5----->|
          |-----W=0, FCN=1, Seq=6----->|
DL Enable |-----W=0, FCN=0, Seq=7--X-->|
      (no ACK)
          |-----W=1, FCN=6, Seq=8----->|
          |-----W=1, FCN=5, Seq=9----->|
          |-----W=1, FCN=4, Seq=10---->|
DL Enable |-----W=1, FCN=7, Seq=11---->| Missing Fragment W=0 => FCN= 5, 3 and 0
          |<------ ACK, W=0, C=0 ------| Bitmap:1010110
          |-----W=0, FCN=5, Seq=12---->|
          |-----W=0, FCN=3, Seq=13---->|
DL Enable |-----W=0, FCN=0, Seq=14---->| All fragments received
          |<------ ACK, W=1, C=1 ------| C=1
        (End)
```

In this case, there are losses in both the first (W=0) and second (W=1) window.
The retransmission cycles (after the All-1 is send, not in intermediate windows)
should always finish with an All-0 (if this message was lost) or with an All-1.
This is required for the sender to open a reception window so the receiver
can send an ACK. 
Else there is no way for the Receiver to send an ACK,
if All-1 message is lost, then an ACK timeout happen 
and an ACK is resend.
```text
                 Sender                            Receiver
          |-----W=0, FCN=6 (110), Seq=1----->|
          |-----W=0, FCN=5 (101), Seq=2--X-->|
          |-----W=0, FCN=4 (100), Seq=3----->|
          |-----W=0, FCN=3 (011), Seq=4--X-->|
          |-----W=0, FCN=2 (010), Seq=5----->|
          |-----W=0, FCN=1 (001), Seq=6----->|
DL enable |-----W=0, FCN=0 (000), Seq=7--X-->|
     (no ACK)
          |-----W=1, FCN=6 (110), Seq=8--X-->|
          |-----W=1, FCN=5 (101), Seq=9----->|
          |-----W=1, FCN=4 (011), Seq=10-X-->|
DL enable |-----W=1, FCN=7 (111), Seq=11---->| Missing Fragment W=0 => FCN= 5, 3 and 0
          |<--------- ACK, W=0, C=0 ---------| Bitmap:1010110
          |-----W=0, FCN=5 (101), Seq=12---->|
          |-----W=0, FCN=3 (011), Seq=13---->|
DL enable |-----W=0, FCN=0 (000), Seq=14---->| Missing Fragment W=1 => FCN= 6 and 4
          |<--------- ACK, W=1, C=0 ---------| Bitmap:0100001
          |-----W=1, FCN=6 (110), Seq=15---->|
          |-----W=1, FCN=4 (011), Seq=16---->| All fragments received
DL enable |-----W=1, FCN=7 (111), Seq=17---->|
          |<--------- ACK, W=1, C=1 ---------| C=1
        (End)
```

Similar case as above, but with less fragments in the second window (W=1)

```text
                 Sender                            Receiver
          |-----W=0, FCN=6 (110), Seq=1----->|
          |-----W=0, FCN=5 (101), Seq=2--X-->|
          |-----W=0, FCN=4 (100), Seq=3----->|
          |-----W=0, FCN=3 (011), Seq=4--X-->|
          |-----W=0, FCN=2 (010), Seq=5----->|
          |-----W=0, FCN=1 (001), Seq=6----->|
DL enable |-----W=0, FCN=0 (000), Seq=7--X-->|
       (no ACK)
          |-----W=1, FCN=6 (110), Seq=8--X-->|
DL enable |-----W=1, FCN=7 (111), Seq=9----->| Missing Fragment W=0 => FCN= 5, 3 and 0
          |<--------- ACK, W=0, C=0 ---------| Bitmap:1010110
          |-----W=0, FCN=5 (101), Seq=10---->|
          |-----W=0, FCN=3 (011), Seq=11---->|
DL enable |-----W=0, FCN=0 (000), Seq=12---->| Missing Fragment W=1 => FCN= 6 and 4
          |<--------- ACK, W=1, C=0 ---------| Bitmap:0000001
          |-----W=1, FCN=6 (110), Seq=15---->| All fragments received
DL enable |-----W=1, FCN=7 (111), Seq=17---->|
          |<--------- ACK, W=1, C=1 ---------| C=1
        (End)
```

#### Cases where the All-0 or All-1 are lost

##### The last window only has the All-1


```text
                 Sender                            Receiver
          |-----W=0, FCN=6 (110), Seq=1----->|
          |-----W=0, FCN=5 (101), Seq=2----->|
          |-----W=0, FCN=4 (100), Seq=3----->|
          |-----W=0, FCN=3 (011), Seq=4----->|
          |-----W=0, FCN=2 (010), Seq=5----->|
          |-----W=0, FCN=1 (001), Seq=6----->|
DL enable |-----W=0, FCN=0 (000), Seq=7----->| 
     (no ACK)
DL enable |-----W=1, FCN=7 (111), Seq=8----->| 
          |<--------- ACK, W=1, C=1 ---------| 
        (End)
```
The sequence number between the last 2 messages is consecutive. 

##### Only the All-1 in last window is received

```text
                 Sender                            Receiver
          |-----W=0, FCN=6 (110), Seq=1----->|
          |-----W=0, FCN=5 (101), Seq=2----->|
          |-----W=0, FCN=4 (100), Seq=3----->|
          |-----W=0, FCN=3 (011), Seq=4----->|
          |-----W=0, FCN=2 (010), Seq=5----->|
          |-----W=0, FCN=1 (001), Seq=6----->|
DL enable |-----W=0, FCN=0 (000), Seq=7--X-->| Bitmap: 1111110
     (no ACK)
          |-----W=1, FCN=6 (110), Seq=8--X-->|
          |-----W=1, FCN=5 (101), Seq=9--x-->|
          |-----W=1, FCN=4 (011), Seq=10-X-->|
DL enable |-----W=1, FCN=7 (111), Seq=11---->| 
          |<--------- ACK, W=0, C=0 ---------| Bitmap:1111110
          |-----W=0, FCN=5 (101), Seq=13---->|
          |-----W=0, FCN=3 (011), Seq=14---->|
DL enable |-----W=0, FCN=0 (000), Seq=15---->| 
          |<--------- ACK, W=1, C=0 ---------| Bitmap:0000001
          |-----W=1, FCN=6 (110), Seq=17---->|
          |-----W=1, FCN=4 (011), Seq=18---->| All fragments received
DL enable |-----W=1, FCN=7 (111), Seq=19---->|
          |<--------- ACK, W=1, C=1 ---------| C=1
        (End)
```




#### Case ACK is lost:

SCHC over sigfox does not implement the SCHC ACK REQ message, 
instead it uses the SCHC All-1 message to request an ACK, when required.

```text
        Sender                      Receiver
          |-----W=0, FCN=6, Seq=1----->|
          |-----W=0, FCN=5, Seq=2----->|
          |-----W=0, FCN=4, Seq=3----->|
          |-----W=0, FCN=3, Seq=4----->|
          |-----W=0, FCN=2, Seq=5----->|
          |-----W=0, FCN=1, Seq=6----->|
DL Enable |-----W=0, FCN=0, Seq=7----->|
      (no ACK)
          |-----W=1, FCN=6, Seq=8----->|
          |-----W=1, FCN=5, Seq=9----->|
          |-----W=1, FCN=4, Seq=10---->|
DL Enable |-----W=1, FCN=7, Seq=11---->| All fragments received
          |<------ ACK, W=1, C=1 ---X--| C=1
DL Enable |-----W=1, FCN=7, Seq=13---->| RESEND ACK
          |<------ ACK, W=1, C=1 ------| C=1
        (End)
```
The number of times an ACK will be requested is determined by the
 MAX_ACK_REQUESTS. The recommended value in SCHC over sigfox is 5.
 
 
 #### Case SCHC Sender-Abort:

The sender may need to send a sender abort to abort current communication.
This may happen, for example, if the All-1 has been sent MAX_ACK_REQUESTS times.

```text
        Sender                      Receiver
          |-----W=0, FCN=6, Seq=1----->|
          |-----W=0, FCN=5, Seq=2----->|
          |-----W=0, FCN=4, Seq=3----->|
          |-----W=0, FCN=3, Seq=4----->|
          |-----W=0, FCN=2, Seq=5----->|
          |-----W=0, FCN=1, Seq=6----->|
DL Enable |-----W=0, FCN=0, Seq=7----->|
      (no ACK)
          |-----W=1, FCN=6, Seq=8----->|
          |-----W=1, FCN=5, Seq=9----->|
          |-----W=1, FCN=4, Seq=10---->|
DL Enable |-----W=1, FCN=7, Seq=11---->| All fragments received
          |<------ ACK, W=1, C=1 ---X--| C=1
DL Enable |-----W=1, FCN=7, Seq=14---->| RESEND ACK  (1)
          |<------ ACK, W=1, C=1 ---X--| C=1
DL Enable |-----W=1, FCN=7, Seq=15---->| RESEND ACK  (2)
          |<------ ACK, W=1, C=1 ---X--| C=1
DL Enable |-----W=1, FCN=7, Seq=16---->| RESEND ACK  (3)
          |<------ ACK, W=1, C=1 ---X--| C=1
DL Enable |-----W=1, FCN=7, Seq=17---->| RESEND ACK  (4)
          |<------ ACK, W=1, C=1 ---X--| C=1
DL Enable |-----W=1, FCN=7, Seq=18---->| RESEND ACK  (5) 
          |<------ ACK, W=1, C=1 ---X--| C=1
DL Enable |----Sender-Abort, Seq=19--->| exit with error condition
        (End)
```

### Case receiver Abort

The reciever may need to send a receiver abort to abort current communication.
This message can only be send after a DL enable.

```text
        Sender                      Receiver
          |-----W=0, FCN=6, Seq=1----->|
          |-----W=0, FCN=5, Seq=2----->|
          |-----W=0, FCN=4, Seq=3----->|
          |-----W=0, FCN=3, Seq=4----->|
          |-----W=0, FCN=2, Seq=5----->|
          |-----W=0, FCN=1, Seq=6----->|
DL Enable |-----W=0, FCN=0, Seq=7----->| 
          |<-------  RECV ABORT -------| under-resourced
       (Error)
```



