import cfg

# -------------------------------- INTERPOLATE ------------------------------- #
# This function will interpolate between the two nearest datapoints by drawing 
# a linear line between them

def interpolate_setpoint():
        # if time less than first point, setpoint is 0
        if (cfg.REFLOW_TIME <= cfg.SETPOINT_LIST[0][0]):
                return 0
        # if time greater than last point, setpoint is 0
        if (cfg.REFLOW_TIME >= (cfg.SETPOINT_LIST[-1][0])):
                return 0
        
        # increment the current index until the next index's time is greater
        while (True):
                if ((cfg.CURRENT_INDEX+1) < len(cfg.SETPOINT_LIST)):
                        if ((cfg.SETPOINT_LIST[cfg.CURRENT_INDEX][0]) <= cfg.REFLOW_TIME):
                                if ((cfg.SETPOINT_LIST[cfg.CURRENT_INDEX+1][0]) > cfg.REFLOW_TIME):
                                        # Use a linear approximation to interpolate
                                        if ((cfg.SETPOINT_LIST[cfg.CURRENT_INDEX][0] == 
                                                cfg.SETPOINT_LIST[cfg.CURRENT_INDEX+1][0])):
                                                raise(ZeroDivisionError())
                                        X1, Y1 = cfg.SETPOINT_LIST[cfg.CURRENT_INDEX]
                                        X2, Y2 = cfg.SETPOINT_LIST[cfg.CURRENT_INDEX+1]
                                        X = cfg.REFLOW_TIME
                                        Y = (((Y1-Y2)/(X1-X2))*(X-X1)+Y1) # Linear Approximation
                                        return Y
                                else: 
                                        # need to increment the index because the next point is too soon
                                        cfg.CURRENT_INDEX += 1
                                        continue

                        else: 
                                return 0 # return 0 and wait until the time is greater
                        
                else: 
                        return 0 # this means our index is on the last point, heaters should be off
# ---------------------------------------------------------------------------- #

# ---------------------------------- INIT_FF --------------------------------- #\
# initialize the loaded values and determine delay and slope range
def init_ff():
        minimum_slope = 100
        maximum_slope = -1
        minimum_delay = 1000
        maximum_delay = -1
        minimum_dc = 100
        maximum_dc = 0
        for i in cfg.TMP_RISE_LIST:
                if (i[0] > maximum_dc):
                        maximum_dc = i[0]
                if (i[0] < minimum_dc): 
                        minimum_dc = i[0]

                if (i[1] > maximum_slope):
                        maximum_slope = i[1]
                if (i[1] < minimum_slope): 
                        minimum_slope = i[1]

                if (i[2] > maximum_delay):
                        maximum_delay = i[2]
                if (i[2] < minimum_delay): 
                        minimum_delay = i[2]
        cfg.TMP_DC_RANGE = (minimum_dc, maximum_dc)
        cfg.TMP_SLOPE_RANGE = (minimum_slope, maximum_slope)
        cfg.TMP_DELAY_RANGE = (minimum_delay, maximum_delay)
        return
# ---------------------------------------------------------------------------- #

# ----------------------------- INTERPOLATE_FF_DC ---------------------------- #
# takes in a 
def interpolate_ff_dc(slope):
        pass
# ---------------------------------------------------------------------------- #