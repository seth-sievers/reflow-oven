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
float TMP_BUF[4];
unsigned long int LAST_SAMPLE_MS = 0; 
unsigned long int NUM_SAMPLES = 0; 
unsigned int BUF_INDEX = 0; 
double TMP_C = 0; 

char BUF[16]; // Serial Receive Buffer
char TMP_STR_BUF[16]; //buffer to separate input data

// State machine
short STATE = 0;
unsigned long int LAST_MESSAGE_MS = 0;  
unsigned long int REFLOW_START_MS = 0; 
unsigned long int PREWARM_START_MS = 0; 

// Heater
const float PWM_FREQ = 0.5; 
SoftPWM HEATER_PWM(10, PWM_FREQ); 
double HEATER_DC = 0;
double SETPOINT = 0; 
double PID_OUTPUT = 0; 
double KP = 20;
double KI = 0;
double KD = 0; 
PID PID_CONTROLLER(&TMP_C, &PID_OUTPUT, &SETPOINT, KP, KI, KD, P_ON_E, DIRECT);
float FF_DC = 0;

/* -------------------------------------------------------------------------- */

/* ----------------------------- FUNCTION_STUBS ----------------------------- */
float sum(const float array[4]); 
void clearBuf(char array[], const short LEN); 
void sendData(unsigned long int time, float tmpC, float setP, float ff_dc);
void sendDataSigned(long int time, float tmpC, float setP, float ff_dc);
bool isNumeric (const char array[], const short LEN);
void readData();
/* -------------------------------------------------------------------------- */

/* ---------------------------------- SETUP --------------------------------- */
void setup() 
{
        // Setup serial and buffer
        Serial.begin(115200);
        Serial.setTimeout(500); 
        clearBuf(BUF, 16); 

        // Heater and Control 
        HEATER_PWM.setDC(0); 
        PID_CONTROLLER.SetMode(MANUAL);
        PID_CONTROLLER.SetOutputLimits(0, 100);
        PID_CONTROLLER.SetSampleTime(500);
        
        pinMode(4, OUTPUT); 
        digitalWrite(4, LOW);

}
/* -------------------------------------------------------------------------- */

/* ---------------------------------- LOOP ---------------------------------- */
void loop()
{
        // Heater software PWM update
        HEATER_PWM.update();

        // Sample every 250ms and recompute temperatures
        if ((millis() - LAST_SAMPLE_MS) > 250){
                BUF_INDEX = (NUM_SAMPLES % 4);
                TMP_BUF[BUF_INDEX] = TMP.readTempC();
                LAST_SAMPLE_MS = millis(); 
                NUM_SAMPLES++; 
                TMP_C = sum(TMP_BUF)/4.0;
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
                                Serial.readBytesUntil('\n', BUF, 16);
                                if (strcmp(BUF, "ACK") == 0) {
                                        STATE = 1; 
                                        PREWARM_START_MS = millis();
                                } else {
                                        clearBuf(BUF, 16); 
                                }
                        }
                        break; 
                case 1:
                        /* --------------------- PREWARM -------------------- */
                        // time of <0 tells host to send first setpoint and specifies 
                        // oven is prewarming and timer has not started
                        if ((millis() - LAST_MESSAGE_MS) > 250) {
                                sendDataSigned(-1000, TMP_C, SETPOINT, FF_DC);
                                LAST_MESSAGE_MS = millis(); 
                        }
                        readData(); 

                        // lock out state logic to allow variables to be set initially
                        if ((millis() - PREWARM_START_MS) > 500){
                                if (SETPOINT > TMP_C) {
                                        HEATER_PWM.setDC(100); 
                                } else {
                                        HEATER_PWM.setDC(0);
                                        STATE = 2; 
                                }
                        }
                        // if (Serial.available() > 0) {
                        //         Serial.readBytesUntil('\n', BUF, 12);
                        //         if (isNumeric(BUF, 12)) {
                        //                 SETPOINT = atof(BUF); 
                        //                 HEATER_PWM.setDC(100);
                        //                 clearBuf(BUF, 12);
                        //         } else {
                        //                 clearBuf(BUF, 12); 
                        //         }
                        //         if (TMP_C > SETPOINT) {
                        //                 HEATER_PWM.setDC(0);
                        //                 REFLOW_START_MS = millis(); 
                        //                 PID_CONTROLLER.SetMode(AUTOMATIC);
                        //                 STATE = 2; 
                        //         }
                        // }
                        break; 
                case 2:
                        /* --------------- FEEDFORWARD_RAMPUP --------------- */
                        // time of 0 specifies that controller is in feedforward ramp mode
                        // this means that the oven needs time to begin heating the
                        // elements to fulfill the feedforward controller
                        // once the host sends a negative ff_dc, the reflow cycle will begin
                        if ((millis() - LAST_MESSAGE_MS) > 250) {
                                sendDataSigned(0, TMP_C, SETPOINT, FF_DC);
                                LAST_MESSAGE_MS = millis(); 
                        }
                        readData(); 
                        if (FF_DC >= 0) {
                                HEATER_PWM.setDC(FF_DC); 
                        } else {
                                HEATER_PWM.setDC(0); 
                                REFLOW_START_MS = millis(); 
                                PID_CONTROLLER.SetMode(AUTOMATIC);
                                STATE = 3;  
                        }
                        break; 
                case 3:
                        /* --------------------- REFLOW --------------------- */
                        // PID controller takes over and follows setpoint sent
                        // by host script in combination with compensation FF controller
                        if ((millis() - LAST_MESSAGE_MS) > 250) {
                                sendData((millis() - REFLOW_START_MS), 
                                        TMP_C, SETPOINT, FF_DC);
                                LAST_MESSAGE_MS = millis(); 
                        }
                        readData(); 
                        PID_CONTROLLER.Compute(); 
                        // combine FF DC with PID output but clamp to 100
                        if ((FF_DC + PID_OUTPUT) >= 100) {
                                HEATER_DC = 100; 
                        } else {
                                HEATER_DC = (FF_DC + PID_OUTPUT);
                        }
                        HEATER_PWM.setDC(HEATER_DC);
                        break; 
        }
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

void clearBuf(char array[], const short LEN)
{
        for (short i = 0; i < LEN; i++) 
        {
                array[i] = '\0'; 
        }
        return; 
}

void sendData(unsigned long int time, float tmpC, float setP, float ff_dc)
{
        Serial.print(time/1000.0);
        Serial.print(F(","));
        Serial.print(tmpC); 
        Serial.print(F(","));
        Serial.print(setP);
        Serial.print(F(","));
        Serial.println(ff_dc); 
        return; 
}

void sendDataSigned(long int time, float tmpC, float setP, float ff_dc)
{
        Serial.print(time/1000.0);
        Serial.print(F(","));
        Serial.print(tmpC); 
        Serial.print(F(","));
        Serial.print(setP);
        Serial.print(F(","));
        Serial.println(ff_dc); 
        return; 
}

bool isNumeric (const char array[], const short LEN)
{
        bool isANumber = false; 
        for (short i = 0; i < LEN; i++)
        {
                if (array[i] != '\0') {
                        if (isDigit(array[i]) || (array[i] == '-') || ((array[i] == '.') && (i != 0))) {
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

void readData()
{
        if (Serial.available() > 0) {
                // read entire data string into buffer
                clearBuf(BUF, 16);
                clearBuf(TMP_STR_BUF, 16); 
                Serial.readBytesUntil('\n', BUF, 16);
                // read the setpoint from the string
                short i = 0;
                short j = 0; 
                for (; i < 16; i++)
                {
                        if ((BUF[i] == '\0') || (BUF[i] == '\n')) {
                                clearBuf(BUF, 16);
                                clearBuf(TMP_STR_BUF, 16);  
                                return; // stop malformed data
                        }
                        if (BUF[i] == ',') {
                                i++; 
                                break; // go on to ff_dc
                        } else {
                                TMP_STR_BUF[j] = BUF[i];
                                j++; 
                        }
                }
                if (isNumeric(TMP_STR_BUF, 16)) {
                        SETPOINT = atof(TMP_STR_BUF); 
                }

                // read the ff_dc
                clearBuf(TMP_STR_BUF, 16); 
                j = 0; 
                for (; i < 16; i++) 
                {
                        if ((BUF[i] == '\n') || (BUF[i] == ',')) {
                                clearBuf(BUF, 16);
                                clearBuf(TMP_STR_BUF, 16);  
                                return; // stop malformed data
                        }
                        if (BUF[i] == '\0') {
                                break; 
                        } else {
                                TMP_STR_BUF[j] = BUF[i]; 
                                j++;
                        }
                }
                if (isNumeric(TMP_STR_BUF, 16)) {
                        FF_DC = atof(TMP_STR_BUF); 
                }
        }
        return; 
}
/* -------------------------------------------------------------------------- */

