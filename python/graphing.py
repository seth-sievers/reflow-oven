from globals import *
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from multiprocessing import Process
from operator import itemgetter
import math



# --------------------------------- RUNGRAPH --------------------------------- #
# Based off of https://stackoverflow.com/questions/51949185/non-blocking-matplotlib-animation
def runGraph():
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
        
        # create setpoint line
        xs_sp = []
        ys_sp = []
        for k in SETPOINT_LIST:
                xs_sp.append(k[0])
                ys_sp.append(k[1])
        setpoint_line, = ax.plot(xs_sp, ys_sp, color='xkcd:purple', linestyle=':')

        #create temp line
        tmp_line, = ax.plot(XS_TMP, YS_TMP, color='xkcd:red', linestyle='solid')

        # labels
        plt.title('REFLOW TEMPERATURE')
        plt.xlabel('Time (s)')
        plt.ylabel('Temp (C)')
        setpoint_line.set_label('Target')
        ax.legend(loc='upper left')

        # This function updates temp line with new data and is called by FuncAnimation()
        def animate(i):
                tmp_line.set_xdata(XS_TMP)
                tmp_line.set_ydata(YS_TMP)
                return tmp_line,

        # Setup FuncAnimation
        ani = animation.FuncAnimation(fig, animate, interval=10, blit=True,
                                        cache_frame_data=False)
        plt.show()

        return
# ---------------------------------------------------------------------------- #

##########################
if __name__ == '__main__':
        runGraph()
##########################