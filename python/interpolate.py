import cfg

# -------------------------------- INTERPOLATE ------------------------------- #
# This function will interpolate between the two nearest datapoints by drawing 
# a linear line between them

def interpolate_setpoint():
        # if time less than first point, setpoint is 0
        if (float(cfg.REFLOW_TIME) <= 10):
                print(cfg.TMP_C)
                print(f'Time less than first {0 >= cfg.REFLOW_TIME}, cfg.REFLOW_TIME:{cfg.REFLOW_TIME}')
                return 0
        # if time greater than last point, setpoint is 0
        if (cfg.REFLOW_TIME >= (cfg.SETPOINT_LIST[-1][0])):
                print('Time greater than last')
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
                                        print(f'X1:{X1},Y1:{Y1},X2:{X2},Y2:{Y2},X:{X},Y:{Y}')
                                        return Y
                                else: 
                                        # need to increment the index because the next point is too soon
                                        print('increment the index and try again')
                                        cfg.CURRENT_INDEX += 1
                                        continue

                        else: 
                                print('return 0 and wait until time is greater')
                                return 0 # return 0 and wait until the time is greater
                        
                else: 
                        print('Index on last point')
                        return 0 # this means our index is on the last point, heaters should be off


# ---------------------------------------------------------------------------- #