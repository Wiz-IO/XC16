# Uploader
## Based of reverse engineering of Pickit4 protocol
( The project is a work in progress, there may be bugs... )

Python Depends: intelhex & pyusb ( libusb-1.0.dll )<br> 
Download and Put "libusb-1.0.dll" in python.exe folder ( maybe need only for Windows )<br>
( for PlatformIO ...user/.platformio/penv/Scripts/ )<br>
https://github.com/libusb/libusb/releases<br>


## Protocol ( PIC mode)

Must work for PicKit4, Snap, PKOB...<br>
( tested with PK4 and PIC24FJ )

```
 00 01 00 00                    COMMAND TYPE
 00 00 00 00                    SEQUENCE ( always zero )
 38 01 00 00                    FULL PACKET SIZE
 00 00 00 00                    TRANSFER LENGTH ( if )
 08 00 00 00                    PARAMS SIZE
 18 01 00 00                    SCRIPT SIZE
 00 00 80 00 EE 0B 00 00        PARAMS[n] ( if )
 E0 00 02 04 E0 00 02 04 ...    SCRIPT[n] ( if )
```
The first 16 bytes is named HEADER<br>
COMMAND TYPE is command for: simple packet, packet with upload or download data ... etc<br>
The SCRIPTs is byte-code operations ... as function with PARAMS<br>

other info: TODO
