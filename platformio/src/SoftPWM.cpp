#include "SoftPWM.h"
#include "Arduino.h"

/* ------------------------- SOFT_PWM_IMPLEMENTATION ------------------------ */
SoftPWM::SoftPWM(const unsigned short PIN, const unsigned short FREQ)
{
        pin = PIN; 
        freq = FREQ; 
        changed = true; 
        pinMode(pin, OUTPUT);
        digitalWrite(pin, LOW); 
        return; 
}

void SoftPWM::update()
{
        // if variables updated recompute timings
        if (changed) {
                period = ceil(1000000.0/freq);
                onPeriod = ceil((DutyCycle/100.0)*period);
                offPeriod = period - onPeriod; 
                changed = false;

                // if the dutycycle or frequency changes, recompute using stored lastRunUS value
                // should mitigate pwm lag when changing from a slow frequency or high DC
                switch (!state) // we want the previous state
                {
                        case 0:
                                nextRunUS = lastRunUS + onPeriod; 
                                break; 
                        case 1: 
                                nextRunUS = lastRunUS + offPeriod; 
                                break;
                }
        }
        
        //PWM state machine 
        if (micros() > nextRunUS) {
                if (DutyCycle == 0 ) {
                        digitalWrite(pin, LOW); 
                        state = 1; 
                }
                switch (state)
                {
                        case 0:
                                // on 
                                digitalWrite(pin, HIGH); 
                                nextRunUS = micros() + onPeriod; 
                                state = 1; 
                                break; 
                        case 1: 
                                // off
                                digitalWrite(pin, LOW); 
                                nextRunUS = micros() + offPeriod; 
                                state = 0; 
                                break; 
                }
                lastRunUS = micros(); 
        } else {
                unsigned long currentUS = micros(); 
                if ((currentUS < nextRunUS) && ((nextRunUS - currentUS) > 1000000000UL)) {
                        //catch any micros() overflow, one cycle will be malformed
                        switch (!state) //we want the previous state
                        {
                                case 0:
                                        nextRunUS = micros() + onPeriod; 
                                        break; 
                                case 1:
                                        nextRunUS = micros() + offPeriod; 
                                        break; 
                        }
                }
        }
        
}

void SoftPWM::setFreq(const unsigned short FREQ)
{
        freq = FREQ; 
        changed = true; 
        return; 
}

void SoftPWM::setDC(const float DC)
{
        if (DC != DutyCycle) {
                DutyCycle = DC; 
                changed = true; 
        }
        return; 
}
/* -------------------------------------------------------------------------- */