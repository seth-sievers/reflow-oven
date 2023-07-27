import cfg
from operator import itemgetter

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
        cfg.TMP_RISE_LIST.sort(key=itemgetter(0)) # sort the list based off of DC
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

# --------------------------- INTERPOLATE_FF_DELAY --------------------------- #
def interpolate_ff_delay(dc):
        # if out of bounds return 0
        if ((cfg.TMP_DC_RANGE[0] > dc) or (cfg.TMP_DC_RANGE[1] < dc)):
                return 0
        i = 0
        # iterate through calibration list until current points are found
        for i in range(len(cfg.TMP_RISE_LIST)-1):
                if (cfg.TMP_RISE_LIST[i][0] == dc):
                        return cfg.TMP_RISE_LIST[i][2]
                elif ((cfg.TMP_RISE_LIST[i][0] < dc) and (cfg.TMP_RISE_LIST[i+1][0] > dc)):
                        #use linear approximation of i and i+1
                        X1, z, Y1 = cfg.TMP_RISE_LIST[i]
                        X2, z, Y2 = cfg.TMP_RISE_LIST[i+1]
                        X = dc
                        Y = (((Y1-Y2)/(X1-X2))*(X-X1)+Y1)
                        return Y
                elif (cfg.TMP_RISE_LIST[i+1][0] == dc):
                        return cfg.TMP_RISE_LIST[i+1][0]
                else:
                        print('Error: (interpolate_ff_delay) No delay Found')
        return 0
# ---------------------------------------------------------------------------- #

# ----------------------------- INTERPOLATE_FF_DC ---------------------------- #
def interpolate_ff_dc(slope):
        # handle bounds
        if (cfg.TMP_SLOPE_RANGE[0] > slope):
                return 0
        elif (cfg.TMP_SLOPE_RANGE[1] < slope):
                return cfg.TMP_DC_RANGE[1]
        
        # make a list of elements sorted by slope
        slope_cal_list = sorted(cfg.TMP_RISE_LIST, key=itemgetter(1))

        # iterate through interpolating between points
        for i in range(len(slope_cal_list)-1):
                if (slope_cal_list[i][1] == slope):
                        return slope_cal_list[i][0]
                elif ((slope_cal_list[i][1] < slope) and (slope_cal_list[i+1][1] > slope)):
                        Y1, X1, = slope_cal_list[i]
                        Y2, X2, = slope_cal_list[i+1]
                        X = slope
                        Y = (((Y1-Y2)/(X1-X2))*(X-X1)+Y1)
                        return Y
                elif (slope_cal_list[i+1][1] == slope):
                        return slope_cal_list[i+1][1]
                else: 
                        print('Error: (interpolate_ff_dc) No dc found')
        return 0
# ---------------------------------------------------------------------------- #

# ----------------------------------- SLOPE ---------------------------------- #
def slope(i1, i2):
        return ((cfg.SETPOINT_LIST[i1][1]-cfg.SETPOINT_LIST[i2][1])/ \
                (cfg.SETPOINT_LIST[i1][0]-cfg.SETPOINT_LIST[i2][0]))
# ---------------------------------------------------------------------------- #

# ---------------------------- GET_SETPOINT_SLOPE ---------------------------- #
# this will be horribly inefficient but should be okay(ish), index caching potential here
def get_setpoint_slope(t):
        if (t > cfg.SETPOINT_LIST[-1][0]):
                return 0
        elif (t < cfg.SETPOINT_LIST[0][0]):
                return 0
        # seek through list for time
        for i in range(len(cfg.SETPOINT_LIST)-1):
                if (cfg.SETPOINT_LIST[i][0] == t):
                        #handle rare instances
                        if (i == 0): return 0 
                        if (i > (len(cfg.SETPOINT_LIST)-2)): return 0
                        # if on point, then return average of two nearest slopes
                        return (sum((slope(i-1, i), slope(i, i+1)))/2)
                elif ((cfg.SETPOINT_LIST[i][0] < t) and (cfg.SETPOINT_LIST[i+1][0] > t)):
                        return slope(i, i+1)
                elif (cfg.SETPOINT_LIST[i+1][0] == t):
                        if ((i+1) == 0): return 0 
                        if ((i+1) > (len(cfg.SETPOINT_LIST)-2)): return 0
                        return (sum((slope(i,i+1), slope(i+1, i+2)))/2)
        return 0
# ---------------------------------------------------------------------------- #

# ------------------------------ CALCULATE_FF_DC ----------------------------- #
def calculate_ff_dc(): 
        # iterate through setpoint curve on time range of interest to determine
        # the highest requested DC by the FF compensation curve
        maximum_dc = 0
        for i in range(cfg.TMP_DELAY_RANGE[0], cfg.TMP_DELAY_RANGE[1]+1, 1):
                t = i + cfg.REFLOW_TIME
                if ((t > cfg.SETPOINT_LIST[-1][0]) or (t < cfg.SETPOINT_LIST[0][-1])):
                        continue

                #at time t calculate the dc and then check delay to see if its valid
                current_slope = get_setpoint_slope(t)
                dc = interpolate_ff_dc(current_slope)
                delay = interpolate_ff_delay(dc)

                if ()




        return maximum_dc
# ---------------------------------------------------------------------------- #