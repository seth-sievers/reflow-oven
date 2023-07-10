//Author: Seth Sievers
//Date: 7/9/23
//Purpose: This Arduino Program will communicate with the python based host 
//      controller script for the purpose of controlling a modified toaster oven
//      reflow oven

#include "Arduino.h"
#include "MAX6675.h"
#include "Stdint.h"
#include "SoftPWM.h"
#include "PID_v1.h"

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
double TMP_C = 0; 
float TMP_UPPER_C = 0; 
float TMP_LOWER_C = 0; 

char BUF[8]; // Serial Receive Buffer

// State machine
short STATE = 0;
unsigned long int LAST_MESSAGE_MS = 0;  
unsigned long int REFLOW_START_MS = 0; 

// Heater
const unsigned short PWM_FREQ = 2; 
SoftPWM UPPER_HEATER_PWM(10, PWM_FREQ); 
SoftPWM LOWER_HEATER_PWM(9, PWM_FREQ); 
double UPPER_HEATER_DC = 0;
double LOWER_HEATER_DC = 0; 
double SETPOINT = 0; 
double PID_OUTPUT = 0; 
double KP = 10;
double KI = 0;
double KD = 0; 
PID PID_CONTROLLER(&TMP_C, &PID_OUTPUT, &SETPOINT, KP, KI, KD, P_ON_E, DIRECT);

unsigned long DC = 0; 
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
        Serial.setTimeout(500); 
        clearBuf(BUF); 

        // Heaters
        UPPER_HEATER_PWM.setDC(0); 
        LOWER_HEATER_PWM.setDC(0); 
        PID_CONTROLLER.SetMode(MANUAL);
        PID_CONTROLLER.SetOutputLimits(0, 200);
        PID_CONTROLLER.SetSampleTime(500);
        

        pinMode(4, OUTPUT); 
        digitalWrite(4, LOW);

}
/* -------------------------------------------------------------------------- */

/* ---------------------------------- LOOP ---------------------------------- */
void loop()
{
        // Heater software PWM update
        UPPER_HEATER_PWM.update();
        LOWER_HEATER_PWM.update();

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
                        if ((millis() - LAST_MESSAGE_MS) > 250) {
                                Serial.println(F("READY")); 
                                LAST_MESSAGE_MS = millis(); 
                        }
                        if (Serial.available() > 0) {
                                Serial.readBytesUntil('\n', BUF, 8);
                                if (strcmp(BUF, "ACK") == 0) {
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
                        if ((millis() - LAST_MESSAGE_MS) > 500) {
                                sendData(0, TMP_C, TMP_UPPER_C, TMP_LOWER_C);
                                LAST_MESSAGE_MS = millis(); 
                        }
                        if (Serial.available() > 0) {
                                Serial.readBytesUntil('\n', BUF, 8);
                                if (isNumeric(BUF)) {
                                        SETPOINT = atof(BUF); 
                                        UPPER_HEATER_PWM.setDC(100);
                                        LOWER_HEATER_PWM.setDC(100);
                                        clearBuf(BUF);
                                } else {
                                        clearBuf(BUF); 
                                }
                                if (TMP_C > SETPOINT) {
                                        UPPER_HEATER_PWM.setDC(0);
                                        LOWER_HEATER_PWM.setDC(0);
                                        REFLOW_START_MS = millis(); 
                                        PID_CONTROLLER.SetMode(AUTOMATIC);
                                        STATE = 2; 
                                }
                        }
                        break; 
                case 2:
                        /* --------------------- REFLOW --------------------- */
                        // PID controller takes over and follows setpoint sent
                        // by host script
                        PID_CONTROLLER.Compute(); 
                        UPPER_HEATER_DC = PID_OUTPUT/2.0;
                        LOWER_HEATER_DC = PID_OUTPUT/2.0;
                        UPPER_HEATER_PWM.setDC(UPPER_HEATER_DC);
                        LOWER_HEATER_PWM.setDC(LOWER_HEATER_DC); 

                        if ((millis() - LAST_MESSAGE_MS) > 500) {
                                sendData((millis() - REFLOW_START_MS), 
                                        TMP_C, TMP_UPPER_C, TMP_LOWER_C);
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
                        digitalWrite(4, HIGH); 
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

