# Fragmentation examples 

## SCHC-over-Sigfox implementation

The Sigfox Sequence Number (Seq) represented is only available at the receiver, and its represented as 
it is used to know if there are missing fragments between the All-1 and the penultimate SCHC fragment.
This because is not possible for the receiver to know (without a RCS), if there are missing fragment
between the last received SCHC fragment and the All-1.

### No-ACK Mode
#### Uplink No-ACK Mode

The FCN field indicates the size of the data packet. 
The first fragment is marked with FCN = X-1, where X is the number of fragments the message is splitted.
All fragments are marked with decreasing FCN values.
Last packet fragment is marked with the FCN = All-1 (1111).

```text
        Sender               Receiver
          |-------FCN=6 (0110), Seq=1-------->|
          |-------FCN=5 (0101), Seq=2-------->|
          |-------FCN=4 (0100), Seq=3-------->|
          |-------FCN=3 (0011), Seq=4-------->|
          |-------FCN=2 (0010), Seq=5-------->|
          |-------FCN=1 (0001), Seq=6-------->|
          |-------FCN=15 (1111), Seq=7------->| All fragments received
        (End)
```

```text
        Sender               Receiver
          |-------FCN=6, Seq=1-------->|
          |-------FCN=5, Seq=2----X--->|
          |-------FCN=4, Seq=3-------->|
          |-------FCN=3, Seq=4-------->|
          |-------FCN=2, Seq=5-------->|
          |-------FCN=1, Seq=6-------->|
          |-------FCN=15, Seq=7------->| Missing Fragment
        (End)
```


### ACK-on-Error Mode


#### Case No losses

```text
        Sender               Receiver
          |-----W=0, FCN=6, Seq=1----->|
          |-----W=0, FCN=5, Seq=2----->|
          |-----W=0, FCN=4, Seq=3----->|
          |-----W=0, FCN=3, Seq=4----->|
          |-----W=0, FCN=2, Seq=5----->|
          |-----W=0, FCN=1, Seq=6----->|
          |-----W=0, FCN=0, Seq=7----->|
      (no ACK)
          |-----W=1, FCN=6, Seq=8----->|
          |-----W=1, FCN=5, Seq=9----->|
          |-----W=1, FCN=4, Seq=10---->|
          |-----W=1, FCN=7, Seq=11---->| All fragments received
          |<------ ACK, W=1, C=1 ------| C=1
        (End)
```

#### Case Fragments lost in first window:

```text
        Sender               Receiver
          |-----W=0, FCN=6, Seq=1----->|
          |-----W=0, FCN=5, Seq=2--X-->|
          |-----W=0, FCN=4, Seq=3----->|
          |-----W=0, FCN=3, Seq=4----->|
          |-----W=0, FCN=2, Seq=5--X-->|
          |-----W=0, FCN=1, Seq=6----->|
          |-----W=0, FCN=0, Seq=7----->| Missing Fragments W=0 => FCN=5, Seq=2 and FCN=2, Seq=5
          |<------ ACK, W=0, C=0 ------| Bitmap:1011011
          |-----W=0, FCN=5, Seq=8----->|
          |-----W=0, FCN=2, Seq=9----->|
      (no ACK)
          |-----W=1, FCN=6, Seq=10---->|
          |-----W=1, FCN=5, Seq=11---->|
          |-----W=1, FCN=4, Seq=12---->|
          |-----W=1, FCN=7, Seq=13---->| All fragments received
          |<------ ACK, W=1, C=1 ------| C=1
        (End)
```




Case :

The All-0 of window 0 is lost, therefore the Receiver waits for next All-X message to generate 
the corresponding ACK, notifying the absence of the All-0 of window 0.

```text
        Sender                      Receiver
          |-----W=0, FCN=6, Seq=1----->|
          |-----W=0, FCN=5, Seq=2----->|
          |-----W=0, FCN=4, Seq=3----->|
          |-----W=0, FCN=3, Seq=4----->|
          |-----W=0, FCN=2, Seq=5----->|
          |-----W=0, FCN=1, Seq=6----->|
          |-----W=0, FCN=0, Seq=7--X-->|
      (no ACK)
          |-----W=1, FCN=6, Seq=8----->|
          |-----W=1, FCN=5, Seq=9----->|
          |-----W=1, FCN=4, Seq=10---->|
          |-----W=1, FCN=7, Seq=11---->| Missing Fragment W=0, FCN=0, Seq=7
          |<------ ACK, W=0, C=0 ------| Bitmap:1111110
          |-----W=0, FCN=0, Seq=12---->| All fragments received
          |<------ ACK, W=1, C=1 ------| C=1
        (End)
```


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

```text
                 Sender                            Receiver
                   |-----W=0, FCN=6 (110), Seq=1----->|
                   |-----W=0, FCN=5 (101), Seq=2--X-->|
                   |-----W=0, FCN=4 (100), Seq=3----->|
                   |-----W=0, FCN=3 (011), Seq=4--X-->|
                   |-----W=0, FCN=2 (010), Seq=5----->|
                   |-----W=0, FCN=1 (001), Seq=6----->|
        DL enable  |-----W=0, FCN=0 (000), Seq=7--X-->|
               (no ACK)
                   |-----W=1, FCN=6 (110), Seq=8--X-->|
                   |-----W=1, FCN=5 (101), Seq=9----->|
                   |-----W=1, FCN=4 (011), Seq=10-X-->|
        DL enable  |-----W=1, FCN=7 (111), Seq=11---->| Missing Fragment W=0 => FCN= 5, 3 and 0
                   |<--------- ACK, W=0, C=0 ---------| Bitmap:1010110
                   |-----W=0, FCN=5 (101), Seq=12---->|
                   |-----W=0, FCN=3 (011), Seq=13---->|
        DL enable  |-----W=0, FCN=0 (000), Seq=14---->| Missing Fragment W=1 => FCN= 6 and 4
                   |<--------- ACK, W=1, C=0 ---------| Bitmap:0100001
                   |-----W=1, FCN=6 (110), Seq=15---->|
                   |-----W=1, FCN=4 (011), Seq=16---->| All fragments received
        DL enable  |-----W=1, FCN=7 (111), Seq=17---->|
                   |<--------- ACK, W=1, C=1 ---------| C=1
                 (End)
```
The retransmission cycles (after the All-1 is send, that is, not in intermediate windows)
should always finish with an All-0 (if this message was lost) or with an All-1.
This is required so that the sender opens a reception window so that the receiver
can send an ACK. Else there is no way for the Receiver to confirm if some fragments
have been received, if All-1 message is lost, then an ACK timeout happen 
and an ACK is resend.


```text
                 Sender                            Receiver
                   |-----W=0, FCN=6 (110), Seq=1----->|
                   |-----W=0, FCN=5 (101), Seq=2--X-->|
                   |-----W=0, FCN=4 (100), Seq=3----->|
                   |-----W=0, FCN=3 (011), Seq=4--X-->|
                   |-----W=0, FCN=2 (010), Seq=5----->|
                   |-----W=0, FCN=1 (001), Seq=6----->|
        DL enable  |-----W=0, FCN=0 (000), Seq=7--X-->|
               (no ACK)
                   |-----W=1, FCN=6 (110), Seq=8--X-->|
        DL enable  |-----W=1, FCN=7 (111), Seq=9----->| Missing Fragment W=0 => FCN= 5, 3 and 0
                   |<--------- ACK, W=0, C=0 ---------| Bitmap:1010110
                   |-----W=0, FCN=5 (101), Seq=10---->|
                   |-----W=0, FCN=3 (011), Seq=11---->|
        DL enable  |-----W=0, FCN=0 (000), Seq=12---->| Missing Fragment W=1 => FCN= 6 and 4
                   |<--------- ACK, W=1, C=0 ---------| Bitmap:0000001
                   |-----W=1, FCN=6 (110), Seq=15---->| All fragments received
        DL enable  |-----W=1, FCN=7 (111), Seq=17---->|
                   |<--------- ACK, W=1, C=1 ---------| C=1
                 (End)
```