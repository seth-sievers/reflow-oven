from globals import *

# -------------------------------- INTERPOLATE ------------------------------- #
# This function will interpolate between the two nearest datapoints by drawing 
# a linear line between them

def interpolate_setpoint():
        global REFLOW_TIME
        # if time less than first point, setpoint is 0
        if (float(REFLOW_TIME) <= 10):
                print(TMP_C)
                print(f'Time less than first {0 >= REFLOW_TIME}, REFLOW_TIME:{REFLOW_TIME}')
                return 0
        # if time greater than last point, setpoint is 0
        if (REFLOW_TIME >= (SETPOINT_LIST[-1][0])):
                print('Time greater than last')
                return 0
        
        # increment the current index until the next index's time is greater
        while (True):
                if ((CURRENT_INDEX+1) < len(SETPOINT_LIST)):
                        if ((SETPOINT_LIST[CURRENT_INDEX][0]) <= REFLOW_TIME):
                                if ((SETPOINT_LIST[CURRENT_INDEX+1][0]) > REFLOW_TIME):
                                        # Use a linear approximation to interpolate
                                        if ((SETPOINT_LIST[CURRENT_INDEX][0] == 
                                                SETPOINT_LIST[CURRENT_INDEX+1][0])):
                                                raise(ZeroDivisionError())
                                        X1, Y1 = SETPOINT_LIST[CURRENT_INDEX]
                                        X2, Y2 = SETPOINT_LIST[CURRENT_INDEX+1]
                                        X = REFLOW_TIME
                                        Y = (((Y1-Y2)/(X1-X2))*(X-X1)+Y1) # Linear Approximation
                                        print(f'X1:{X1},Y1:{Y1},X2:{X2},Y2:{Y2},X:{X},Y:{Y}')
                                        return Y
                                else: 
                                        # need to increment the index because the next point is too soon
                                        print('increment the index and try again')
                                        CURRENT_INDEX += 1
                                        continue

                        else: 
                                print('return 0 and wait until time is greater')
                                return 0 # return 0 and wait until the time is greater
                        
                else: 
                        print('Index on last point')
                        return 0 # this means our index is on the last point, heaters should be off


# ---------------------------------------------------------------------------- #