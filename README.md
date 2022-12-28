# Microchip XC16 PlatformIO
## 16 bit Arduino ( PIC24, PIC30, dsPIC33 )
_( The project is a work in progress, there may be bugs... )_


>If you want to help / support or treat me to Coffee  [![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=ESUP9LCZMZTD6)

![pic](https://raw.githubusercontent.com/Wiz-IO/LIB/master/images/arduino_pic24f.jpg)

Framework source: https://github.com/Wiz-IO/framework-XC16

## COMPILER<br>
Platform use installed XC16 compiler<br>
For now I use **1.50** ( NOT tested with a larger version. )

1. Install XC16 **v1.50** from the Microchip website

2. Install C++ Compiler ( need for CPP projects and Arduino )<br>
https://github.com/fabio-d/xc16plusplus <br>
https://github.com/fabio-d/xc16plusplus/releases <br>

3. Uploader use "libusb-1.0.dll" https://github.com/libusb/libusb/releases <br>
Put DLL in PlatformIO Python folder ( .platformio/penv/Scripts )

4. Install Platform:<br>
PIO Home > Platforms > Advanced Installation: paste https://github.com/Wiz-IO/XC16


## Problems ?<br>
**In general, C projects ( Baremetal ) should work without problems ( any XC16 versions )** <br>
Should work on Linux & Mac too ... no idea, me: Windows<br>
**ATTENTION** Arduino API is 32 bits, XC16 is 16 bits ( **int** )<br>
Recommended chips ( for Arduino ) with **32k** RAM<br>
I have on hand **PIC24FJ256GB206** & PIC24F16KA301<br>
so, the experiments are with this [boards](https://github.com/Wiz-IO/XC16/blob/main/boards)<br>


## Debugging
challenge, but in some other life...


## UPLOADER<br>
[Integrated uploader, based of reverse engineering of PicKit4 ( GEN4 ) protocol](https://github.com/Wiz-IO/XC16/tree/main/builder/frameworks/uploader)<br>
_must work with PicKit4, Snap... etc_ <br>

Note: for Windows need "libusb-1.0.dll"<br>

Demo: https://www.youtube.com/watch?v=PiL7RAr3POE <br>

**"Plan B"** use MPLAB IPE ( PicKit etc ) - Load HEX, Program<br>



## INI
```ini
[env:WizIO-PIC24FJ256GB206]
platform = XC16
board = WizIO-PIC24FJ256GB206
framework = Arduino ; or Baremetal

;custom_xc16 = C:\Program Files\Microchip\xc16\v1.50 ; select custom version, default is 1.50

;custom_heap = 8129 ; is default

monitor_port = COM26
monitor_speed = 115200
```

## Baremetal
is just a platform name of the C projects here <br>
for CPP projects, rename main.c to main.cpp

## Arduino 
Support: Basic Arduino API, some pins, Serial, Wire, SPI... etc, in process... <br>
Note: SPI phrase is used from Microchip SDK, so, the library use **Spi** 

**Example**
```cpp
#include <Arduino.h>

void blink()
{
    static unsigned int i = 0;
    static uint32_t begin = millis();
    if (millis() - begin > 200)
    {
        begin = millis();
        digitalToggle(LED);
    }
    if (++i > 60000)
    {
        i = 0;
        Serial.print("MILLIS: ");
        Serial.println(millis());
    }
}

void setup()
{
    Serial.begin(115200); // pins 11 & 12
    Serial.println("PIC24F Hello World 2022 Georgi Angelov");
    pinMode(LED, OUTPUT);
}

void loop()
{
    blink();
    if (Serial.available() > 0)
    {
        Serial.print("CHAR: ");
        Serial.write(Serial.read());
        Serial.println();
    }
}
```

![gif](https://raw.githubusercontent.com/Wiz-IO/LIB/master/images/xc16.gif)

<hr>

>If you want to help / support or treat me to Coffee ( 12 Year Old Whisky ) [![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=ESUP9LCZMZTD6)
