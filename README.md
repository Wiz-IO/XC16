# Microchip XC16 PlatformIO

## FOR NOW IS JUST EXPERIMENT !?! <br> 
**and there may be many errors...**


## COMPILER<br>
Platform use installed XC16 compiler<br>
For now I use **1.24**

1. Install C++ Compiler ( need for cpp projects and/or Arduino )<br>
https://github.com/fabio-d/xc16plusplus

2. Install platform:<br>
PIO Home > Platforms > Advanced Installation: paste this git url

## PROBLEMS<br>
Should work on Linux & Mac too... no idea...  me: Windows<br>
The compiler has some quirks... I'm experimenting :)<br>
**ATTENTION** Arduino API is 32 bits, XC16 is 16 bits (int)<br>
I have PIC24FJ256GB206, so, the experiments are with this chip/board<br>

## UPLOADER<br>
MPLAB IPE (PICKIT 3, 4 etc ) - load HEX, Program...

## INI
```ini
[env:WizIO-PIC24FJ256GB206]
platform = XC16
board = WizIO-PIC24FJ256GB206
framework = Arduino

;custom_xc16 C:/Program Files (x86)/Microchip/xc16/v1.2x : select custom version

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
    Serial.begin(115200);
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
