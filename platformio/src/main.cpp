//Author: Seth Sievers
//Date: 7/9/23
//Purpose: This Arduino Program will communicate with the python based host 
//      controller script for the purpose of controlling a modified toaster oven
//      reflow oven

#include "Arduino.h"
#include "MAX6675.h"
#include "Stdint.h"

/* ---------------------------- GLOBAL_VARIABLES ---------------------------- */
// Temperature Vars
MAX6675 TMP(10);
MAX6675 TMP_UPPER(9); 
MAX6675 TMP_LOWER(8); 
float TMP_BUF[4];
float TMP_UPPER_BUF[4];
float TMP_LOWER_BUF[4]; 
unsigned long int LAST_SAMPLE_MS = 0; 
unsigned long int NUM_SAMPLES = 0; 
unsigned int BUF_INDEX = 0; 
float TMP_C = 0; 
float TMP_UPPER_C = 0; 
float TMP_LOWER_C = 0; 

char BUF[8]; // Serial Receive Buffer

// State machine
short STATE = 0;
unsigned long int LAST_READY_MS = 0;  


unsigned long int test_MS = 0; 
/* -------------------------------------------------------------------------- */

/* ----------------------------- FUNCTION_STUBS ----------------------------- */
float sum(const float array[4]); 
/* -------------------------------------------------------------------------- */

/* ---------------------------------- SETUP --------------------------------- */
void setup() 
{
        //setup serial and buffer
        Serial.begin(115200);
        Serial.setTimeout(250); 
        for (short i = 0; i < 8; i++) {
                BUF[i] = '\0'; 
        }

        pinMode(4, OUTPUT); 
        digitalWrite(4, LOW);

}
/* -------------------------------------------------------------------------- */

/* ---------------------------------- LOOP ---------------------------------- */
void loop()
{
        // Sample every 250ms and recompute temperatures
        if ((millis() - LAST_SAMPLE_MS) > 250){
                BUF_INDEX = (NUM_SAMPLES % 4);
                TMP_BUF[BUF_INDEX] = TMP.readTempC();
                TMP_UPPER_BUF[BUF_INDEX] = TMP_UPPER.readTempC();
                TMP_LOWER_BUF[BUF_INDEX] = TMP_LOWER.readTempC(); 
                LAST_SAMPLE_MS = millis(); 
                NUM_SAMPLES++; 
                TMP_C = sum(TMP_BUF)/4.0;
                TMP_UPPER_C = sum(TMP_UPPER_BUF)/4.0;
                TMP_LOWER_C = sum(TMP_LOWER_BUF)/4.0;
        }

        // State machine controlling operation
        switch(STATE)
        {
                case 0:
                        //send READY signal and check for response
                        if ((millis() - LAST_READY_MS) > 100) {
                                Serial.println(F("READY")); 
                                LAST_READY_MS = millis(); 
                        }
                        if ((Serial.available() > 0)) {
                                Serial.readBytesUntil('\n', BUF, 8);
                                if (strcmp(BUF, "ACK") == 0) {
                                        digitalWrite(4,HIGH); 
                                        STATE = 1; 
                                }
                        }
                        break; 
                case 1:
                        break; 
                case 2:
                        break; 
        }








        // if ((millis() - test_MS) > 250){
        //         Serial.print(F("TMP: "));
        //         Serial.print(TMP_C);
        //         Serial.print(F(" TMP_UPPER: "));
        //         Serial.print(TMP_UPPER_C);
        //         Serial.print(F(" TMP_LOWER: "));
        //         Serial.println(TMP_LOWER_C);
        //         test_MS = millis(); 
        // }
}
/* -------------------------------------------------------------------------- */

/* ----------------------------------- SUM ---------------------------------- */
float sum(const float array[4])
{
        float total = 0; 
        for (short i = 0; i < 4; i++) 
        {
                total += array[i]; 
        }
        return total; 
}
/* -------------------------------------------------------------------------- */