#include "Arduino.h"

char buf[8]; 
bool received = false; 

void setup()
{
        // put your setup code here, to run once:
        Serial.begin(115200); 
        pinMode(13, OUTPUT); 
        digitalWrite(13, LOW);
        Serial.setTimeout(100000);
        //initialize the buffer
        for (byte i = 0; i < 8; i++) {
                buf[i] = '\0'; 
        }
}



void loop()
{
        // put your main code here, to run repeatedly:
        /* ------------------------------ test ------------------------------ */
        delay(100);
        if (received == false){
                Serial.println(F("READY"));
        } else {
                Serial.println(buf);
        }
        
        if (Serial.available() > 0) {
                Serial.readBytesUntil('\n', buf, 8); 
                if (strcmp(buf, "ACK") == 0) {
                        digitalWrite(13, HIGH); 
                }
                received++; 
        }
        
        /* ------------------------------------------------------------------ */
}
