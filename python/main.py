'''
Author: Seth Sievers
Date: 7/8/23
Purpose: This script is to be used alongside an arduino script to control and 
        monitor a modified toaster oven for the purpose of reflowing SMD PCB's
'''

import time
import csv
import matplotlib
import multiprocessing
import serial

# ----------------------------- GLOBAL_VARIABLES ----------------------------- #
CSV_FILENAME = ''
# ---------------------------------------------------------------------------- #


# ----------------------------------- MAIN ----------------------------------- #
def main():
        # Get CSV name and verify extension
        print('---REFLOW-HOST-SCRIPT---')
        print('Specify the complete filename for the CSV defined reflow curve')
        CSV_FILENAME = input('CSV Filename: ')
        if (CSV_FILENAME[-4::] != '.csv'):
                CSV_FILENAME += '.csv'



        return
# ---------------------------------------------------------------------------- #

##########################
if __name__ == '__main__':
        main()
##########################