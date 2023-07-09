#include "SoftPWM.h"

/* ------------------------- SOFT_PWM_IMPLEMENTATION ------------------------ */
SoftPWM::SoftPWM(const unsigned short PIN, const unsigned short FREQ)
{
        pin = PIN; 
        freq = FREQ; 
        return; 
}
/* -------------------------------------------------------------------------- */