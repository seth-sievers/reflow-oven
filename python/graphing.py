import cfg
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import threading
from operator import itemgetter
import math
import warnings
import csv

# --------------------------------- RUNGRAPH --------------------------------- #
# Based off of https://stackoverflow.com/questions/51949185/non-bcfg.LOCKing-matplotlib-animation
def runGraph():
        warnings.filterwarnings('ignore', module='graphing')
        # y_lim = max setpoint plus 10%, x_lim = max time plus 10%
        y_len = math.ceil((sorted(cfg.SETPOINT_LIST, key=itemgetter(1), reverse=True)[0][1])*1.1)
        y_range = (20, y_len)
        x_len = math.ceil(cfg.SETPOINT_LIST[-1][0]*1.1)
        x_range = (0, x_len)

        # create figure
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        ax.set_ylim(y_range)
        ax.set_xlim(x_range)
        
        # create setpoint line
        xs_sp = []
        ys_sp = []
        for k in cfg.SETPOINT_LIST:
                xs_sp.append(k[0])
                ys_sp.append(k[1])
        setpoint_line, = ax.plot(xs_sp, ys_sp, color='xkcd:purple', linestyle=':')

        #create temp line
        cfg.LOCK.acquire()
        tmp_line, = ax.plot(cfg.XS_TMP, cfg.YS_TMP, color='xkcd:red', linestyle='solid')
        cfg.LOCK.release()

        # labels
        plt.title('REFLOW TEMPERATURE')
        plt.xlabel('Time (s)')
        plt.ylabel('Temp (C)')
        setpoint_line.set_label('Target')
        tmp_line.set_label('Actual')
        ax.legend(loc='upper left')

        # This function updates temp line with new data and is called by FuncAnimation()
        def animate(i):
                cfg.LOCK.acquire()
                tmp_line.set_xdata(cfg.XS_TMP)
                tmp_line.set_ydata(cfg.YS_TMP)
                cfg.LOCK.release()
                return tmp_line,

        # Setup FuncAnimation
        ani = animation.FuncAnimation(fig, animate, interval=250, blit=True,
                                        cache_frame_data=False)
        plt.show()

        # Before terminating save the temperature data for analysis 
        fields = [ [cfg.XS_TMP[i], cfg.YS_TMP[i]] for i in range(len(cfg.XS_TMP))]
        with open('lastrun.csv', 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=',')
                csvwriter.writerows(fields)
        
        return
# ---------------------------------------------------------------------------- #

##########################
if __name__ == '__main__':
        runGraph()
##########################