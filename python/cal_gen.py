'''
Author: Seth Sievers
Date: 7/20/23
Purpose: This script will take in an impulse test .csv data file and the time centerpoint
        of the target slope and extrapolate outward to determine the average slope
        and the delay until '~steady state' slope is reached. 

        It operates with a rolling average containing a subset of the line and a
        static average containing the entire set of currently discovered line points. 
        The static average is computed and then the rolling average of (x-1)
        previous points already contained in the static average and one additional point
        is computed and compared to the static average. If the % difference is greater
        than the tolerance the line has reached one of its ends. The line is expanded 
        simultaneously from the center point in each direction alternating computations.
'''

import csv

# ---------------------------------- CONFIG ---------------------------------- #
# Note: Both the tolerance and Sample count determines the sensitivity
# Specify the % tolerance in decimal form that if exceeded means the line has curved
TOLERANCE = 0.2

# Number of datapoints averaged together in the rolling average
ROLL_AVG_SAMPLES = 30

# ---------------------------------------------------------------------------- #

# ---------------------------------- GLOBALS --------------------------------- #
DATA_LIST = []
START_DELAY = None
CENTER_INDEX = None
DC = None
RIGHT_BOUNDED = False
RIGHT_OFFSET = 0
LEFT_BOUNDED = False
LEFT_OFFSET = 0
STATIC_AVERAGE = None
# ---------------------------------------------------------------------------- #

# ----------------------------------- SLOPE ---------------------------------- #
def slope(i1, i2):
        return ((DATA_LIST[i1][1]-DATA_LIST[i2][1])/(DATA_LIST[i1][0]-DATA_LIST[i2][0]))
# ---------------------------------------------------------------------------- #

# ------------------------------- OFFSET_VALID ------------------------------- #
def offset_valid(i):
        if (i > 0):
                return ((i + CENTER_INDEX) < len(DATA_LIST))
        elif (i < 0):
                return ((CENTER_INDEX - i) >= 0)
        else:
                return True
# ---------------------------------------------------------------------------- #

# ---------------------------- COMPUTE_STATIC_AVG ---------------------------- #
def compute_static_avg(left_index, right_index):
        tmp_slope_list = []
        for i in range((left_index), (right_index), 1):
                tmp_slope_list.append(slope(i,i+1))
        return sum(tmp_slope_list)/len(tmp_slope_list)
# ---------------------------------------------------------------------------- #

# ----------------------------------- MAIN ----------------------------------- #
def main():
        global CENTER_INDEX
        global DATA_LIST
        global RIGHT_OFFSET
        global RIGHT_BOUNDED
        global LEFT_OFFSET
        global LEFT_BOUNDED
        global START_DELAY
        global STATIC_AVERAGE
        global DC

        # Read in the data points and do basic validation, throwing out bad points
        # time,temp
        csv_filename = input('Enter complete path & filename to the data .csv file: ')
        #csv_filename = 'testRuns/calibrationRuns/100DC.csv'
        with open(csv_filename, newline='') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',')
                last_line_time = -1
                last_line_temp = -1
                i = 0
                for row in csvreader:
                        i += 1
                        row = (float(row[0]), float(row[1]))
                        if ((row[0] >= 0) and (row[0] > last_line_time) and (row[1] >= 0) and (row[1] != last_line_temp)):
                                DATA_LIST.append(row)
                                last_line_time = row[0]
                                last_line_temp = row[1]
        print(f'Loaded {len(DATA_LIST)} of {i} data points.\n')

        # record DC
        DC = float(input('Enter duty cycle data was captured at (0-100): '))
        print()

        # Determine the nearest index of the center point
        center_time = float(input('Enter the approximate time of center of ' \
                                        'constant slope line: '))
        for i in range(len(DATA_LIST)-1): 
                if (DATA_LIST[i][0] == center_time):
                        CENTER_INDEX = i
                        break
                elif (DATA_LIST[i+1][0] == center_time):
                        CENTER_INDEX = i
                        break
                elif ((DATA_LIST[i][0] < center_time) and (DATA_LIST[i+1][0] > center_time)):
                        if (abs(DATA_LIST[i][0]-center_time) < abs(DATA_LIST[i+1][0]-center_time)):
                                CENTER_INDEX = i
                                break
                        else: 
                                CENTER_INDEX = i+1
        print(f'Index {CENTER_INDEX} with time of {DATA_LIST[CENTER_INDEX][0]:.2f}s' \
                f' is closest to {center_time:.2f}s\n')
        
        # Record delay before impulse starts
        START_DELAY = float(input('Enter the delay before the impulse started: '))
        print()

        # Set the offsets based off of inital ROLL_AVG_SAMPLES 
        RIGHT_OFFSET = ROLL_AVG_SAMPLES
        LEFT_OFFSET = -ROLL_AVG_SAMPLES
        if ((not offset_valid(RIGHT_OFFSET)) or (not offset_valid(LEFT_OFFSET))):
                print(f'Initial Offsets of {LEFT_OFFSET} and {RIGHT_OFFSET} Not Valid')
                raise IndexError

        # Begin main computation loop
        state = True 
        while ((not RIGHT_BOUNDED) or (not LEFT_BOUNDED)):
                # Compute the current static average
                STATIC_AVERAGE = compute_static_avg(CENTER_INDEX + LEFT_OFFSET, RIGHT_OFFSET + CENTER_INDEX)

                # Alternate between expanding left and right side, checking if bounds have been reached
                if (state):
                        # Right side
                        # increment the right index by one and compare static avg to rolling
                        RIGHT_OFFSET += 1
                        if (not offset_valid(RIGHT_OFFSET)):
                                print(f'Offset {RIGHT_OFFSET} in main loop is not valid')
                                raise IndexError
                        left_bound = (CENTER_INDEX + (RIGHT_OFFSET - ROLL_AVG_SAMPLES))
                        right_bound = (CENTER_INDEX + RIGHT_OFFSET)
                        roll_avg = compute_static_avg(left_bound, right_bound)
                        print(f'T: {DATA_LIST[CENTER_INDEX+RIGHT_OFFSET][0]}, S:{STATIC_AVERAGE}, R:{roll_avg}', end=' :')
                        if (abs((abs(STATIC_AVERAGE) - abs(roll_avg)) / STATIC_AVERAGE) <= TOLERANCE):
                                # new index is good, keep it and then update static avg 
                                print('Right Good')
                                STATIC_AVERAGE = compute_static_avg(CENTER_INDEX+LEFT_OFFSET, RIGHT_OFFSET+CENTER_INDEX)
                        else: 
                                # new index is bad, discard it and set bounded
                                print('Right Bad')
                                RIGHT_OFFSET -= 1
                                RIGHT_BOUNDED = True

                        state = LEFT_BOUNDED # If left is bounded then do not switch to that state 
                else:
                        # Left side 
                        # increment (decrement) left index and compare static to roll. avg
                        LEFT_OFFSET -= 1
                        if (not offset_valid(LEFT_OFFSET)):
                                print(f'Offset {LEFT_OFFSET} in main loop is not valid')
                                raise IndexError
                        left_bound = (CENTER_INDEX + LEFT_OFFSET)
                        right_bound = (CENTER_INDEX + LEFT_OFFSET) + ROLL_AVG_SAMPLES
                        roll_avg = compute_static_avg(left_bound, right_bound)
                        print(f'T: {DATA_LIST[CENTER_INDEX+LEFT_OFFSET][0]}, S:{STATIC_AVERAGE}, R:{roll_avg}', end=' :')
                        if (abs((abs(STATIC_AVERAGE) - abs(roll_avg)) / STATIC_AVERAGE) <= TOLERANCE):
                                # new index good, keep it and update static avg
                                print('Left Good')
                                STATIC_AVERAGE = compute_static_avg(CENTER_INDEX+LEFT_OFFSET, RIGHT_OFFSET+CENTER_INDEX)
                        else:
                                # new index is bad, discard it and set bounded
                                print('Left Bad')
                                LEFT_OFFSET += 1
                                LEFT_BOUNDED = True
                        
                        state = not RIGHT_BOUNDED
        print(f' Computed Average: {STATIC_AVERAGE}')
        print('---CALIBRATION-CONSTANT---')
        leftmost_index = CENTER_INDEX + LEFT_OFFSET
        print(f'{DC},{STATIC_AVERAGE:.2f},{(DATA_LIST[leftmost_index][0]-START_DELAY):.2f}')
        print('--------------------------')



# ---------------------------------------------------------------------------- #

##########################
if __name__ == '__main__':
        main()
##########################