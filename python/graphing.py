import matplotlib.pyplot as plt
import matplotlib.animation as animation
from multiprocessing import Process
from operator import itemgetter
from globals import *
import math

# --------------------------------- RUNGRAPH --------------------------------- #
# Based off of https://stackoverflow.com/questions/51949185/non-blocking-matplotlib-animation
def runGraph():
        print('Opening Plot')

        # y_lim = max setpoint plus 10%, x_lim = max time plus 10%
        y_len = math.ceil((sorted(SETPOINT_LIST, key=itemgetter(1), reverse=True)[0][1])*1.1)
        y_range = (20, y_len)
        x_len = math.ceil(SETPOINT_LIST[-1][0]*1.1)
        x_range = (0, x_len)

        # create figure
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        ax.set_ylim(y_range)
        ax.set_xlim(x_range)
        
        # create setpoint curve
        xs_sp = []
        ys_sp = []
        for k in SETPOINT_LIST:
                xs_sp.append(k[0])
                ys_sp.append(k[1])
        setpoint_line, = ax.plot(xs_sp, ys_sp, color='xkcd:purple', linestyle=':')
        setpoint_line.set_label('Target')

        #legend
        ax.legend(loc='upper left')

        # labels
        plt.title('REFLOW TEMPERATURE')
        plt.xlabel('Time (s)')
        plt.ylabel('Temp (C)')
        plt.show()


# ---------------------------------------------------------------------------- #



##########################
if __name__ == '__main__':
        runGraph()
##########################