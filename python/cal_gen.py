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
TOLERANCE = 0.05

# Number of datapoints averaged together in the rolling average
ROLL_AVG_SAMPLES = 10

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

# ----------------------------------- MAIN ----------------------------------- #
def main():
        # Read in the data points and do basic validation, throwing out bad points
        # time,temp
        csv_filename = input('Enter complete path & filename to the data .csv file: ')
        with open(csv_filename, newline='') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',')
                last_line_time = -1
                i = 0
                for row in csvreader:
                        i += 1
                        row = (float(row[0]), float(row[1]))
                        if ((row[0] >= 0) and (row[0] > last_line_time) and (row[1] >= 0)):
                                DATA_LIST.append(row)
                                last_line_time = row[0]
        print(f'Loaded {len(DATA_LIST)} of {i} data points.\n')

        # record DC
        DC = float(input('Enter duty cycle data was captured at: '))
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
                print('Initial Offsets Not Valid')
                raise IndexError

        # Begin main computation loop
        while ((not RIGHT_BOUNDED) and (not LEFT_BOUNDED)):
                # Compute the current static average



# ---------------------------------------------------------------------------- #

##########################
if __name__ == '__main__':
        main()
##########################