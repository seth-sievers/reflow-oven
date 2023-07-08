import serial
import time

#test pySerial by opening COM3 and reading from it 
ser = serial.Serial('COM3', 9600)

# ----------------------------------- READ ----------------------------------- #
# while True:
#         b_line = ser.readline()
#         line = b_line.decode('ASCII')
#         print(line, end='')
# ---------------------------------------------------------------------------- #

# ----------------------------------- WRITE ---------------------------------- #
print(ser.write(b'a'))
time.sleep(2)
ser.close()
# ---------------------------------------------------------------------------- #
