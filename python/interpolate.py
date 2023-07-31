import cfg
from operator import itemgetter
import math
import time

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
        maximum_dc = -1
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
        if ((cfg.TMP_DC_RANGE[0] > dc)):
                #!print('lower than dc bound')
                return 0
        if (cfg.TMP_DC_RANGE[1] < dc):
                #!print('higher than dc bound')
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
                        if (Y < cfg.TMP_DELAY_RANGE[0]): return cfg.TMP_DELAY_RANGE[0]
                        if (Y > cfg.TMP_DELAY_RANGE[1]): return cfg.TMP_DELAY_RANGE[1]
                        return Y
                elif (cfg.TMP_RISE_LIST[i+1][0] == dc):
                        return cfg.TMP_RISE_LIST[i+1][2]
        #!print('defaulting to zero')
        return 0
# ---------------------------------------------------------------------------- #

# ----------------------------- INTERPOLATE_FF_DC ---------------------------- #
def interpolate_ff_dc(slope):
        # handle bounds
        if (cfg.TMP_SLOPE_RANGE[0] > slope):
                #!print('lower than minimum bound')
                return 0
        elif (cfg.TMP_SLOPE_RANGE[1] < slope):
                #!print(f'returning upper bound: {cfg.TMP_DC_RANGE[1]}')
                return cfg.TMP_DC_RANGE[1]
        
        # make a list of elements sorted by slope
        slope_cal_list = sorted(cfg.TMP_RISE_LIST, key=itemgetter(1))

        # iterate through interpolating between points
        for i in range(len(slope_cal_list)-1):
                if (slope_cal_list[i][1] == slope):
                        return slope_cal_list[i][0]
                elif ((slope_cal_list[i][1] < slope) and (slope_cal_list[i+1][1] > slope)):
                        Y1, X1, z = slope_cal_list[i]
                        Y2, X2, z = slope_cal_list[i+1]
                        X = slope
                        Y = (((Y1-Y2)/(X1-X2))*(X-X1)+Y1)
                        return Y
                elif (slope_cal_list[i+1][1] == slope):
                        return slope_cal_list[i+1][1]
        #!print('none found, defaulting')
        return 0
# ---------------------------------------------------------------------------- #

# ----------------------------------- SLOPE ---------------------------------- #
def slope(i1, i2):
        return ((cfg.SETPOINT_LIST[i1][1]-cfg.SETPOINT_LIST[i2][1])/ \
                (cfg.SETPOINT_LIST[i1][0]-cfg.SETPOINT_LIST[i2][0]))
# ---------------------------------------------------------------------------- #

# --------------------------------- SLOPE_AVG -------------------------------- #
def slope_avg(i):
        # returns the average slope between points on either side of the target
        max_dt = 1.5
        
        #calculate the offsets to achieve max_dt in either direction
        left_offset = 0
        right_offset = 0
        while (((cfg.SETPOINT_LIST[i][0]-cfg.SETPOINT_LIST[i+left_offset][0] ) < max_dt) \
                and ((left_offset-1+i) > 0)):
                left_offset -= 1
        else:
                left_offset += 1
        try:
                while (((cfg.SETPOINT_LIST[i+right_offset][0]-cfg.SETPOINT_LIST[i][0]) < max_dt) \
                        and ((right_offset+i+1) < (len(cfg.SETPOINT_LIST)))):
                        right_offset += 1
                else:
                        right_offset -= 1
        except:
                #!print(f'i:{i}, right_offset:{right_offset}')
                raise ValueError

        # check if bounds are valid and if not fall back on old method
        if ((i+left_offset) < 0):
                if ((i + 1) < len(cfg.SETPOINT_LIST)):
                        return slope(i, i+1)
        if ((i+right_offset) >= len(cfg.SETPOINT_LIST)):
                if ((i + 1) < len(cfg.SETPOINT_LIST)):
                        return slope(i, i+1)
                
        
        # perform the average
        slope_list = []
        for j in range((i+left_offset), (i+right_offset), 1):
                slope_list.append(slope(j, j+1))
        return (sum(slope_list)/(right_offset-left_offset))

# ---------------------------------------------------------------------------- #

# ---------------------------- GET_SETPOINT_SLOPE ---------------------------- #
# this will be horribly inefficient but should be okay(ish), index caching potential here
def get_setpoint_slope(t):
        if (t > cfg.SETPOINT_LIST[-1][0]):
                return (0, i)
        elif (t < cfg.SETPOINT_LIST[0][0]):
                return (0, i)
        # seek through list for time
        for i in range(len(cfg.SETPOINT_LIST)-1):
                if (cfg.SETPOINT_LIST[i][0] == t):
                        #handle rare instances
                        if (i == 0): return (0, i) 
                        # if on point, then return average of two nearest slopes
                        return (slope_avg(i), i)
                elif ((cfg.SETPOINT_LIST[i][0] < t) and (cfg.SETPOINT_LIST[i+1][0] > t)):
                        return (slope_avg(i), i)
                elif (cfg.SETPOINT_LIST[i+1][0] == t):
                        if ((i+1) == 0): return (0, i)
                        return (slope_avg(i+1), i)
        return (0, i)
# ---------------------------------------------------------------------------- #

# ------------------------------ CALCULATE_FF_DC ----------------------------- #
def calculate_ff_dc(): 
        # iterate through setpoint curve on time range of interest to determine
        # the highest requested DC by the FF compensation curve
        maximum_dc = 0
        dc = 0
        #math.floor(cfg.TMP_DELAY_RANGE[0]) # starting from 5 onward prevents early shutoff
        for i in range(10, math.ceil(cfg.TMP_DELAY_RANGE[1]+1), 1):
                t = i + cfg.REFLOW_TIME
                if ((t > cfg.SETPOINT_LIST[-1][0]) or (t < cfg.SETPOINT_LIST[0][0])):
                        continue

                # at time t calculate the dc and then check delay to see if its valid
                current_slope, slope_index = get_setpoint_slope(t)
                #!print(f'{round(t)}: {current_slope}', end=' ')
                dc = interpolate_ff_dc(current_slope)
                if (dc > 100):
                        dc = 100
                delay = interpolate_ff_delay(dc)

                # The warmer the heater is the quicker it responds
                # Compensate this roughly linear relation with the line calculated in
                # 'delayCompensationCurve.xlsx'
                approximate_setpoint = cfg.SETPOINT_LIST[slope_index][1]
                calculated_delay_offset = 0.1366*approximate_setpoint - 7.2792
                if ((delay - calculated_delay_offset) < 0):
                        delay = 0
                elif (approximate_setpoint < 175): 
                        delay = delay - calculated_delay_offset
                else:
                        # shorten delay and increase gain to help with short peak
                        delay = delay - 0.75*calculated_delay_offset
                        if (delay < 0): delay = 0 
                        if (1.5*dc < 100):
                                dc = 1.5*dc
                        else:
                                dc = 100
                # Use this for loop to detect the peak setpoint
                if (approximate_setpoint > cfg.PEAK_TMP):
                        cfg.PEAK_TMP = approximate_setpoint
                        cfg.PEAK_TIME = t
                #!print(f'Delay is {delay:.0f}, time is {cfg.REFLOW_TIME:.0f}, i is: {i}, value is: {abs(i) < abs(delay)}')

                # if the delay for that DC has not been reached then discard
                if (delay < 0): delay = 0
                if (abs(i) < (abs(delay)+1)): # +1 so that rounding doesn't mess with result
                        if (abs(dc) > maximum_dc):
                                maximum_dc = abs(dc)
                #!else: 
                        #!if (maximum_dc == 0):
                                #!print(f'delay is bad: d{delay}, i{i} [{math.floor(cfg.TMP_DELAY_RANGE[0])}, {math.ceil(cfg.TMP_DELAY_RANGE[1]+1)}]')

                # disable the ff control if the peak has been crossed
                if ((cfg.REFLOW_TIME > cfg.PEAK_TIME) and (cfg.REFLOW_TIME > 50)):
                        maximum_dc = 0

        if ((time.time() - cfg.LAST_FF_STATE_CHANGE_S) > 2):
                if (((abs(cfg.TMP_C) - abs(cfg.CURRENT_SETPOINT)) > 10) and (cfg.REFLOW_TIME > 20)):
                        if (cfg.FEEDFORWARD_EN):
                                cfg.LAST_FF_STATE_CHANGE_S = time.time()
                                cfg.FEEDFORWARD_EN = False
                else:
                        if (not cfg.FEEDFORWARD_EN):
                                cfg.FEEDFORWARD_EN = True
                                cfg.LAST_FF_STATE_CHANGE_S = time.time()

        if (not cfg.FEEDFORWARD_EN): 
                maximum_dc = 0
        # to prevent run away from ff, disable if > 10c above current setpoint
        # if peak hasn't been reached then bost until it is reached
        if (((cfg.TMP_C - cfg.PEAK_TMP) >= -5) and ((time.time() - cfg.REFLOW_TIME) > 50)):
                cfg.HAS_REACHED_PEAK_SETPOINT = True
        if (not(cfg.HAS_REACHED_PEAK_SETPOINT) and (cfg.PEAK_TIME < cfg.REFLOW_TIME) and ((time.time() - cfg.REFLOW_TIME) > 50)):
                maximum_dc = 100

        return maximum_dc
# ---------------------------------------------------------------------------- #