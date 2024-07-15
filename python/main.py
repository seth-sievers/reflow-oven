'''
Author: Seth Sievers
Date: 7/8/23
Purpose: This script is to be used alongside an arduino script to control and 
        monitor a modified toaster oven for the purpose of reflowing SMD PCB's
'''

import cfg
#from graphing import runGraph #!
import time
import csv
from operator import itemgetter
import serial
import serial.tools.list_ports
import math
import threading
import os
from interpolate import interpolate_setpoint, calculate_ff_dc, init_ff
from gui import run_gui, addToLog

# ----------------------------------- MAIN ----------------------------------- #
def main():
        # Create GUI thread and start
        cfg.T1 = threading.Thread(target=run_gui, name='T1')
        cfg.T1.start()

        # Get CSV name and verify extension
        addToLog('---REFLOW-HOST-SCRIPT---')
        #addToLog('Specify the complete filename for the CSV defined reflow curve')
        #cfg.CSV_FILENAME = input('CSV Filename: ')
        cfg.CSV_FILENAME = '' #! 
        if (cfg.CSV_FILENAME == ''):
                cfg.CSV_FILENAME = 'kesterEP256.csv'
        if (cfg.CSV_FILENAME[-4::] != '.csv'):
                cfg.CSV_FILENAME += '.csv'

        addToLog(cfg.CSV_FILENAME)

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
                addToLog(f'Loaded {i} curve points of which {len(cfg.SETPOINT_LIST)} are valid.')
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
                addToLog(f'Loaded {i} slope rise compensation points')

        # while True:
        #         time.sleep(1)
        #         addToLog('sleeping')
        #         if (not cfg.REFLOW_ACTIVE):
        #                 return 

        # Attempt a connection
        reflow_started = False
        ser = None
        connection_start_time = None
        while (not reflow_started):
                cfg.COM_PORT_LOCK.acquire()
                if (cfg.TO_CONNECT):
                        # Attempt a connection 
                        try: 
                                ser = serial.Serial(cfg.SELECTED_SERIAL_PORT, 115200, timeout=1)
                                addToLog('Waiting for Connection...', end='')
                                connection_start_time = time.time()
                                while (ser.readline().decode('ASCII') != 'READY\r\n'):
                                        if ((time.time() - connection_start_time) > 15):
                                                addToLog('TIMEOUT')
                                                break
                                else: 
                                        addToLog('READY')
                                        reflow_started = True
                                        #cfg.REFLOW_ACTIVE = True 
                                        cfg.HAS_CONNECTED = True
                        except Exception as e:
                                addToLog(f'Error Occurred: {e}')
                        cfg.TO_CONNECT = False
                cfg.COM_PORT_LOCK.release()
                time.sleep(0.1)

        addToLog('PRESS START TO BEGIN REFLOW:')

        # wait to begin
        to_begin = False
        while (not to_begin):
                cfg.ACTIVE_LOCK.acquire()
                if (cfg.REFLOW_ACTIVE):
                        to_begin = True
                cfg.ACTIVE_LOCK.release() 
                time.sleep(0.1) 

        ser.write('ACK\n'.encode('ASCII')) # no newline added by write()
        
        prewarm_started = False
        feedforward_started = False
        state = 0
        reflow_active = True
        last_message_s = 0
        required_ff_time = 0
        prewarm_start_time = 0
        ff_time = 0
        required_ff_dc = 0
        # State Machine Governing Different Operating Modes
        while (reflow_active):
                cfg.ACTIVE_LOCK.acquire()
                if (not cfg.REFLOW_ACTIVE):
                        reflow_active = False
                cfg.ACTIVE_LOCK.release() 
                time.sleep(0.05) # reduce cpu load 
                if (state == 0):
                        # --------------------- PREWARMNG -------------------- #
                        if (not prewarm_started):
                                addToLog('---Prewarm-Started---')
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
                                                addToLog('--------DONE---------')
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
                                        addToLog(f'Board: {cfg.TMP_C:.2f}°C,' \
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
                                addToLog('---FeedForward-Started---')

                                # Calculate time required for ff prior to starting reflow 
                                for i in range(math.floor(-cfg.TMP_DELAY_RANGE[1]), 1, 1):
                                        cfg.REFLOW_TIME = i
                                        if (calculate_ff_dc() == 0):
                                                continue
                                        else:
                                                required_ff_time = abs(i)
                                                addToLog(f'{required_ff_time} seconds required')
                                                ff_time = time.time()
                                                break
                                if (required_ff_time == 0):
                                        addToLog(f'{required_ff_time} seconds required')
                                        ff_time = time.time()
                                feedforward_started = True

                        # read in from serial and if properly formatted store data
                        received = ser.readline().decode('ASCII')
                        received = received.replace('\r', '').replace('\n','')
                        received = received.split(',')
                        if (len(received) == 4): # cull any malformed packets
                                if (round(float(received[0])) > 0):
                                        addToLog('--------DONE---------')
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
                                        addToLog(f'Board: {cfg.TMP_C:.2f}°C,' \
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
                                #!addToLog(f'T:{cfg.REFLOW_TIME:.0f}, {required_ff_dc:.0f}')
                                ser.write(data_str.encode('ASCII'))
                elif (state == 2):
                        # ---------------------- REFLOW ---------------------- #
                        if (not reflow_started):
                                addToLog('---Reflow-Started----')
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
                                commanded_ff_dc = calculate_ff_dc()
                                data_str = f'{str(cfg.CURRENT_SETPOINT)},{str(round(commanded_ff_dc,2))}\n'
                                ser.write(data_str.encode('ASCII'))

                                # print to terminal
                                if ((time.time() - last_message_s) > 5):
                                        addToLog(f'Board: {cfg.TMP_C:.2f}°C,' \
                                                f'   SetP: {received_setpoint:.2f}°C,' \
                                                f'   FF_DC: {received_ff_dc:.2f}%, commanded FF_DC:{commanded_ff_dc:.2f}')
                                        last_message_s = time.time()
                        else: 
                                continue
        else: 
                # when reflow is ended
                data_str = f'{str(0.00)},{str(0.00)}\n'
                ser.write(data_str.encode('ASCII'))

        
        ser.close()
        return
# ---------------------------------------------------------------------------- #

##########################
if __name__ == '__main__':
        main()
        cfg.T1.join()
        os._exit(0)
##########################