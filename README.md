# Microchip XC16 PlatformIO

![pic](https://raw.githubusercontent.com/Wiz-IO/LIB/master/images/arduino_pic24f.jpg)

Framework source: https://github.com/Wiz-IO/framework-XC16

## COMPILER<br>
Platform use installed XC16 compiler<br>
For now I use **1.50** ( NOT tested with a larger version. )

1. Install XC16 **v1.50** from the Microchip website

2. Install C++ Compiler ( need for CPP projects and Arduino )<br>
https://github.com/fabio-d/xc16plusplus <br>
https://github.com/fabio-d/xc16plusplus/releases <br>

3. Install Platform:<br>
PIO Home > Platforms > Advanced Installation: paste https://github.com/Wiz-IO/XC16

## Problems ?<br>
In general, C projects should work without problems ( any XC16 versions )<br>
Should work on Linux & Mac too... no idea...  me: Windows<br>
**ATTENTION** Arduino API is 32 bits, XC16 is 16 bits ( **int** )<br>
Recommended chips ( for Arduino ) with **32k** RAM<br>
Support: Basic Arduino API, some pins, Serial, Wire, SPI... etc, in process...<br>
I have **PIC24FJ256GB206** ( must work with PIC24FJ256GB210 too ), so, the experiments are with this [board](https://github.com/Wiz-IO/XC16/blob/main/boards/WizIO-PIC24FJ256GB206.json)<br>
Change chip from **ini**:
```ini
custom_mcu = 24FJ256GB210
```

## UPLOADER<br>
MPLAB IPE ( PICKIT 3, 4 etc ) - Load HEX, Program<br>
_I can't find a better solution for now..._

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

## Arduino Example
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

>If you want to help / support or treat me to Coffee ( 12 Year Old Whisky ) <br>
[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=ESUP9LCZMZTD6)
