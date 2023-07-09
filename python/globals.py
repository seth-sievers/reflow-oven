import threading
# ----------------------------- GLOBAL_VARIABLES ----------------------------- #
CSV_FILENAME = ''
SETPOINT_LIST = []
XS_TMP = [0]
YS_TMP = [0]
LOCK = threading.Lock()
T1 = threading.Thread()
# ---------------------------------------------------------------------------- #