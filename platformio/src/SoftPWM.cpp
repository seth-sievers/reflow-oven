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
                period = ceil(1.0/freq);
                onPeriod = ceil((DutyCycle/100.0)*period);
                offPeriod = period - onPeriod; 
                changed = false; 
        }
        
        //PWM state machine 
        if (nextRunUS > micros()) {
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
        DutyCycle = DC; 
        changed = true; 
        return; 
}
/* -------------------------------------------------------------------------- */