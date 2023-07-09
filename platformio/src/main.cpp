//Author: Seth Sievers
//Date: 7/9/23
//Purpose: This Arduino Program will communicate with the python based host 
//      controller script for the purpose of controlling a modified toaster oven
//      reflow oven

#include "Arduino.h"
#include "MAX6675.h"
#include "Stdint.h"
#include "SoftPWM.h"

/* ---------------------------- GLOBAL_VARIABLES ---------------------------- */
// Thermocouple Vars
MAX6675 TMP(8);
MAX6675 TMP_UPPER(7); 
MAX6675 TMP_LOWER(6); 
float TMP_BUF[4];
float TMP_UPPER_BUF[4];
float TMP_LOWER_BUF[4]; 
unsigned long int LAST_SAMPLE_MS = 0; 
unsigned long int NUM_SAMPLES = 0; 
unsigned int BUF_INDEX = 0; 
float TMP_C = 0; 
float TMP_UPPER_C = 0; 
float TMP_LOWER_C = 0; 
float SETPOINT = 0; 

char BUF[8]; // Serial Receive Buffer

// State machine
short STATE = 0;
unsigned long int LAST_MESSAGE_MS = 0;  

// Heater
const unsigned short PWM_FREQ = 30; 
SoftPWM UPPER_HEATER_PWM(10, PWM_FREQ); 
SoftPWM LOWER_HEATER_PWM(9, PWM_FREQ); 


unsigned long int test_MS = 0; 
/* -------------------------------------------------------------------------- */

/* ----------------------------- FUNCTION_STUBS ----------------------------- */
float sum(const float array[4]); 
void clearBuf(char array[8]); 
void sendData(unsigned long int time, float tmpC, float tmpUpperC, float tmpLowerC);
bool isNumeric (const char array[8]);
/* -------------------------------------------------------------------------- */

/* ---------------------------------- SETUP --------------------------------- */
void setup() 
{
        // Setup serial and buffer
        Serial.begin(115200);
        Serial.setTimeout(250); 
        clearBuf(BUF); 

        // Heaters
        UPPER_HEATER_PWM.setDC(50); 
        LOWER_HEATER_PWM.setDC(0); 

        pinMode(4, OUTPUT); 
        digitalWrite(4, LOW);

}
/* -------------------------------------------------------------------------- */

/* ---------------------------------- LOOP ---------------------------------- */
void loop()
{
        // Heater software PWM update (needs very low freq)
        UPPER_HEATER_PWM.update();
        LOWER_HEATER_PWM.update(); 
        //digitalWrite(10, HIGH);
        

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
                        /* ---------------- //INITIALIZATION ---------------- */
                        //send READY signal and check for response
                        if ((millis() - LAST_MESSAGE_MS) > 100) {
                                //Serial.println(F("READY")); 
                                LAST_MESSAGE_MS = millis(); 
                        }
                        if (Serial.available() > 0) {
                                Serial.readBytesUntil('\n', BUF, 8);
                                if (strcmp(BUF, "ACK") == 0) {
                                        //digitalWrite(4,HIGH); 
                                        STATE = 1; 
                                } else {
                                        clearBuf(BUF); 
                                }
                        }
                        break; 
                case 1:
                        /* --------------------- PREWARM -------------------- */
                        // time of 0 tells host to send first setpoint and specifies 
                        // oven is prewarming and timer has not started
                        if ((millis() - LAST_MESSAGE_MS) > 100) {
                                sendData(0, TMP_C, TMP_UPPER_C, TMP_LOWER_C);
                                LAST_MESSAGE_MS = millis(); 
                        }
                        if (Serial.available() > 0) {
                                Serial.readBytesUntil('\n', BUF, 8);
                                if (isNumeric(BUF)) {
                                        SETPOINT = atof(BUF); 
                                        clearBuf(BUF);
                                } else {
                                        clearBuf(BUF); 
                                }
                        }
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

/* --------------------------- FUNCTION_DEFINTIONS -------------------------- */
float sum(const float array[4])
{
        float total = 0; 
        for (short i = 0; i < 4; i++) 
        {
                total += array[i]; 
        }
        return total; 
}

void clearBuf(char array[8])
{
        for (short i = 0; i < 8; i++) 
        {
                array[i] = '\0'; 
        }
        return; 
}

void sendData(unsigned long int time, float tmpC, float tmpUpperC, float tmpLowerC)
{
        Serial.print(time/1000.0);
        Serial.print(F(","));
        Serial.print(tmpC); 
        Serial.print(F(","));
        Serial.print(tmpUpperC);
        Serial.print(F(","));
        Serial.println(tmpLowerC); 
}

bool isNumeric (const char array[8])
{
        bool isANumber = false; 
        for (short i = 0; i < 8; i++)
        {
                if (array[i] != '\0') {
                        if (isDigit(array[i]) || ((array[i] == '.') && (i != 0))) {
                                isANumber = true; 
                        } else {
                                isANumber = false; 
                                break; 
                        }
                } else {
                        return isANumber; 
                }
        }
        return isANumber; 
}
/* -------------------------------------------------------------------------- */

