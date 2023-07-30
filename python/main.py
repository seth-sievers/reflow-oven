'''
Author: Seth Sievers
Date: 7/8/23
Purpose: This script is to be used alongside an arduino script to control and 
        monitor a modified toaster oven for the purpose of reflowing SMD PCB's
'''

import cfg
from graphing import runGraph
import time
import csv
from operator import itemgetter
import serial
import math
import threading
import os
from interpolate import interpolate_setpoint, calculate_ff_dc, init_ff

# ----------------------------------- MAIN ----------------------------------- #
def main():
        # Get CSV name and verify extension
        print('---REFLOW-HOST-SCRIPT---')
        print('Specify the complete filename for the CSV defined reflow curve')
        cfg.CSV_FILENAME = input('CSV Filename: ')
        if (cfg.CSV_FILENAME == ''):
                cfg.CSV_FILENAME = 'kesterEP256.csv'
        if (cfg.CSV_FILENAME[-4::] != '.csv'):
                cfg.CSV_FILENAME += '.csv'

        # Open Curve CSV and read into storage list pruning duplicate values
        # time,temp
        with open(cfg.CSV_FILENAME, newline='') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',')
                last_line_time = -1
                i = 0
                for row in csvreader: 
                        i += 1
                        row = (float(row[0]), float(row[1]))
                        if ((row[0] >= 0) and (row[0] > last_line_time) and (row[1] >= 0)):
                                cfg.SETPOINT_LIST.append(row)
                                last_line_time = row[0]
                print(f'Loaded {i} curve points of which {len(cfg.SETPOINT_LIST)} are valid.')
        cfg.SETPOINT_LIST.sort(key=itemgetter(0)) #sorts based off of first element in inner tuple 

        # Read tmp rise list calibration constants into list 
        # dc,slope,delay
        with open('tmp_rise_constants.csv', newline='') as csvfile: 
                csvreader=csv.reader(csvfile, delimiter=',')
                i = 0
                for row in csvreader:
                        i += 1
                        row = (float(row[0]), float(row[1]), float(row[2]))
                        cfg.TMP_RISE_LIST.append(row)
                if (i == 0): 
                        cfg.FEEDFORWARD_EN = False
                init_ff()
                print(f'Loaded {i} slope rise compensation points')

        # Create thread an start
        T1 = threading.Thread(target=runGraph, name='T1')
        T1.start()

        # Open the Serial Port and wait for 'READY'
        ser = serial.Serial('COM4', 115200, timeout=1)
        print('Waiting for Connection...', end='')
        connection_start_time = time.time()
        while (ser.readline().decode('ASCII') != 'READY\r\n'):
                if ((time.time() - connection_start_time) > 15):
                        print('TIMEOUT')
                        break
        else: 
                print('READY')

        input('PRESS ENTER TO BEGIN REFLOW:')
        ser.write('ACK\n'.encode('ASCII')) # no newline added by write()
        
        prewarm_started = False
        feedforward_started = False
        reflow_started = False
        state = 0
        reflow_active = True
        last_message_s = 0
        required_ff_time = 0
        prewarm_start_time = 0
        ff_time = 0
        required_ff_dc = 0
        # State Machine Governing Different Operating Modes
        while (reflow_active):
                if (state == 0):
                        # --------------------- PREWARMNG -------------------- #
                        if (not prewarm_started):
                                print('---Prewarm-Started---')
                                prewarm_start_time = time.time()
                                prewarm_started = True

                        # read in from serial and if properly formatted store data
                        received = ser.readline().decode('ASCII')
                        received = received.replace('\r', '').replace('\n','')
                        received = received.split(',')
                        if (len(received) == 4): # cull any malformed packets
                                #lock out staging logic to allow initialization of values
                                if ((time.time() - prewarm_start_time) > 0.5):
                                        if (round(float(received[0])) >= 0):
                                                print('--------DONE---------')
                                                state = 1 # if time is no longer < zero it is next state
                                                continue

                                # store temps
                                cfg.TMP_C = float(received[1])
                                received_setpoint = float(received[2])
                                received_ff_dc = float(received[3])
                                cfg.XS_TMP.append(0)
                                cfg.YS_TMP.append(cfg.TMP_C)
                                
                                # print to terminal
                                if ((time.time() - last_message_s) > 5):
                                        print(f'Board: {cfg.TMP_C:.2f}°C,' \
                                                f'   SetP: {received_setpoint:.2f}°C,' \
                                                f'   FF_DC: {received_ff_dc:.2f}%')
                                        last_message_s = time.time()

                                # send back first setpoint and ff_dc 
                                cfg.CURRENT_SETPOINT = round(cfg.SETPOINT_LIST[0][1],2)
                                data_str = f'{str(cfg.CURRENT_SETPOINT)},{0}\n'
                                ser.write(data_str.encode('ASCII'))
                        else: 
                                continue
                elif (state == 1):
                        # ---------------- FEEDFORWARD_RAMPUP ---------------- #
                        if (not feedforward_started):
                                print('---FeedForward-Started---')

                                # Calculate time required for ff prior to starting reflow 
                                for i in range(math.floor(-cfg.TMP_DELAY_RANGE[1]), 1, 1):
                                        cfg.REFLOW_TIME = i
                                        if (calculate_ff_dc() == 0):
                                                continue
                                        else:
                                                required_ff_time = abs(i)
                                                print(f'{required_ff_time} seconds required')
                                                ff_time = time.time()
                                                break
                                if (required_ff_time == 0):
                                        print(f'{required_ff_time} seconds required')
                                        ff_time = time.time()
                                feedforward_started = True

                        # read in from serial and if properly formatted store data
                        received = ser.readline().decode('ASCII')
                        received = received.replace('\r', '').replace('\n','')
                        received = received.split(',')
                        if (len(received) == 4): # cull any malformed packets
                                if (round(float(received[0])) > 0):
                                        print('--------DONE---------')
                                        state = 2 # if time is no longer < zero it is next state
                                        continue

                                # store temps
                                cfg.TMP_C = float(received[1])
                                received_setpoint = float(received[2])
                                received_ff_dc = float(received[3])
                                cfg.XS_TMP.append(0)
                                cfg.YS_TMP.append(cfg.TMP_C)
                                
                                # print to terminal 
                                if ((time.time() - last_message_s) > 5):
                                        print(f'Board: {cfg.TMP_C:.2f}°C,' \
                                                f'   SetP: {received_setpoint:.2f}°C,' \
                                                f'   FF_DC: {received_ff_dc:.0f}%')
                                        last_message_s = time.time()
                                
                                # Update reflow time 
                                cfg.REFLOW_TIME += (time.time() - ff_time)
                                ff_time = time.time()
                                required_ff_dc = calculate_ff_dc()
                                if (cfg.REFLOW_TIME >= 0):
                                        required_ff_dc = -1
                                cfg.CURRENT_SETPOINT = round(cfg.SETPOINT_LIST[0][1],2)
                                data_str = f'{str(cfg.CURRENT_SETPOINT)},{round(required_ff_dc,2)}\n'
                                #!print(f'T:{cfg.REFLOW_TIME:.0f}, {required_ff_dc:.0f}')
                                ser.write(data_str.encode('ASCII'))
                elif (state == 2):
                        # ---------------------- REFLOW ---------------------- #
                        if (not reflow_started):
                                print('---Reflow-Started----')
                                reflow_started = True
                        # read in from serial and if properly formatted send back setpoint
                        received = ser.readline().decode('ASCII')
                        received = received.replace('\r', '').replace('\n','')
                        received = received.split(',')
                        if (len(received) == 4): # cull any malformed packets
                                # store temps and send back interpolated set points
                                cfg.REFLOW_TIME = float(received[0])
                                cfg.TMP_C = float(received[1])
                                received_setpoint = float(received[2])
                                received_ff_dc = float(received[3])
                                cfg.XS_TMP.append(cfg.REFLOW_TIME)
                                cfg.YS_TMP.append(cfg.TMP_C)
                                cfg.CURRENT_SETPOINT = round(interpolate_setpoint(),2)
                                data_str = f'{str(cfg.CURRENT_SETPOINT)},{round(calculate_ff_dc(),2)}\n'
                                ser.write(data_str.encode('ASCII'))

                                # print to terminal
                                if ((time.time() - last_message_s) > 5):
                                        print(f'Board: {cfg.TMP_C:.2f}°C,' \
                                                f'   SetP: {received_setpoint:.2f}°C,' \
                                                f'   FF_DC: {received_ff_dc:.2f}%')
                                        last_message_s = time.time()
                        else: 
                                continue
        
        ser.close()
        T1.join()
        return
# ---------------------------------------------------------------------------- #

##########################
if __name__ == '__main__':
        main()
        os._exit(0)
##########################