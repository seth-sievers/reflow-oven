'''
Author: Seth Sievers
Date: 7/8/23
Purpose: This script is to be used alongside an arduino script to control and 
        monitor a modified toaster oven for the purpose of reflowing SMD PCB's
'''

from globals import *
from graphing import runGraph
import time
import csv
from operator import itemgetter
import serial
import math
import threading
import os

# ----------------------------------- MAIN ----------------------------------- #
def main():
        # Get CSV name and verify extension
        print('---REFLOW-HOST-SCRIPT---')
        print('Specify the complete filename for the CSV defined reflow curve')
        CSV_FILENAME = input('CSV Filename: ')
        if (CSV_FILENAME[-4::] != '.csv'):
                CSV_FILENAME += '.csv'
        CSV_FILENAME = 'kesterEP256.csv' #! REMOVE

        # Open CSV and read into storage list pruning duplicate values
        with open(CSV_FILENAME, newline='') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',')
                last_line_time = -1
                i = 0
                for row in csvreader: 
                        i += 1
                        row = (float(row[0]), float(row[1]))
                        if ((row[0] >= 0) and (row[0] > last_line_time) and (row[1] >= 0)):
                                SETPOINT_LIST.append(row)
                                last_line_time = row[0]
                print(f'Loaded {i} points of which {len(SETPOINT_LIST)} are valid.')
        SETPOINT_LIST.sort(key=itemgetter(0)) #sorts based off of first element in inner tuple 

        # Create thread an start
        T1 = threading.Thread(target=runGraph, name='T1')
        T1.start()

        # Open the Serial Port and wait for 'READY'
        ser = serial.Serial('COM3', 115200, timeout=0.25)
        print('Waiting for Connection...', end='')
        start_time = time.time()
        while (ser.readline().decode('ASCII') != 'READY\r\n'):
                if ((time.time() - start_time) > 15):
                        print('TIMEOUT')
                        break
        else: 
                print('READY')

        input('PRESS ENTER TO BEGIN REFLOW')
        ser.write(b'ACK\n') # no newline added by write()
        ser.close()

        T1.join()
        return
# ---------------------------------------------------------------------------- #

##########################
if __name__ == '__main__':
        main()
        os._exit(0)
##########################