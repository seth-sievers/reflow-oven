#ifndef SOFTPWM_H
#define SOFTPWM_H
//Author: Seth Sievers
//Date: 7/9/23
//Purpose: This is a basic software PWM class created to controlling SSR's which 
//      must be controlled with a frequency lower than hardware PWM is capable of.
//      It does not use timers directly and as such can be further optimized. 

/* ----------------------------- SOFT_PWM_CLASS ----------------------------- */
class SoftPWM
{
        public: 
                // Creates a soft PWM generator on the specified pin 
                SoftPWM(const unsigned short PIN, const unsigned short FREQ);
                
                // Updates timings and switches output if necessary. Should be placed
                // in main loop and ran as fast as possible 
                void update();

                // changes set PWM frequency
                void setFreq(unsigned short freq); 

                // changes set PWM DC, 0 is true off
                void setDC(float DC); 

        private: 
                unsigned short pin; 
                unsigned short freq; 
};
/* -------------------------------------------------------------------------- */

#endif 