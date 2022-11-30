# Microchip XC16 PlatformIO

## FOR NOW IS JUST EXPERIMENT !?! <br> 
**and there may be many errors...**

Framework source: https://github.com/Wiz-IO/framework-XC16

## COMPILER<br>
Platform use installed XC16 compiler<br>
For now I use **1.50** ( Tested with 1.24. NOT tested with a larger version. )

1. Install C++ Compiler ( need for CPP projects and Arduino )<br>
https://github.com/fabio-d/xc16plusplus <br>
https://github.com/fabio-d/xc16plusplus/releases <br>

2. Install Platform:<br>
PIO Home > Platforms > Advanced Installation: paste this git url

## PROBLEMS<br>
In general C projects should work without problems<br>
Should work on Linux & Mac too... no idea...  me: Windows<br>
Should work with PIC24H & dsPIC - TODO !!!<br>
The C++ compiler has some quirks... I'm experimenting...<br>
Linker **--gc-sections** makes a problem, no idea why <br>
**ATTENTION** Arduino API is 32 bits, XC16 is 16 bits ( **int** )<br>
I have PIC24FJ256GB206 ( must work with ...GB210 too ), so, the experiments are with this chip / [board](https://github.com/Wiz-IO/XC16/blob/main/boards/WizIO-PIC24FJ256GB206.json)<br> Recommended chips with **32k** RAM<br>
Support: Basic Arduino API, some pins and Serial ( U1 )<br>

## UPLOADER<br>
MPLAB IPE ( PICKIT 3, 4 etc ) - Load HEX, Program...

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
