#include "Arduino.h"
void setup()
{
        // put your setup code here, to run once:
        Serial.begin(9600); 
        pinMode(13, OUTPUT); 
        digitalWrite(13, LOW);
}

void loop()
{
        // put your main code here, to run repeatedly:
        /* ------------------------------ WRITE ------------------------------ */
        delay(250);
        Serial.println(F("READY"));
        /* ------------------------------------------------------------------ */

        /* ------------------------------ READ ------------------------------ */
        // Serial.setTimeout(1000);
        // char buf[8]; 
        // byte numBytes = 0; 

        // //initialize the buffer
        // for (byte i = 0; i < 8; i++) {
        //         buf[i] = '\0'; 
        // }

        // //wait for data sent
        // while (!Serial.available()) {;}

        // //read the data 
        // numBytes = Serial.readBytes(buf, 8); 

        // //send data back for debug
        // while (true)
        // {
        //         Serial.print(numBytes);
        //         Serial.print(' '); 
        //         Serial.println(buf); 
        //         delay(500); 
        // }
        /* ------------------------------------------------------------------ */
        
}
