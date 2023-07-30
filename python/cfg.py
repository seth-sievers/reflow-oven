import threading
# ----------------------------- GLOBAL_VARIABLES ----------------------------- #
CSV_FILENAME = ''
SETPOINT_LIST = []
TMP_C = 0
#TMP_UPPER_C = 0
#TMP_LOWER_C = 0
REFLOW_TIME = 0
XS_TMP = [0]
YS_TMP = [0]
LOCK = threading.Lock()
T1 = threading.Thread()
CURRENT_INDEX = 0
FEEDFORWARD_EN = True
TMP_RISE_LIST = [] 
TMP_SLOPE_RANGE = []
TMP_DELAY_RANGE = []
TMP_DC_RANGE = []
PEAK_TMP = 75
PEAK_TIME = 100000
CURRENT_SETPOINT = None
# ---------------------------------------------------------------------------- #