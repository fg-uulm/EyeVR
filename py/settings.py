import os
import numpy as np
import time

ROOT = os.path.normpath(os.path.dirname(__file__))

'''Output data for sockets'''
OUT_TRACKDATA = {}

OUT_IMGPROC = np.zeros((320, 240, 3), np.uint8)
OUT_IMGRAW = np.zeros((320, 240, 3), np.uint8)

# colors
OUT_IMGPROC[:] = 50
OUT_IMGRAW[:] = 170

'''Settings dictionary'''
SETTINGS = {}
SETTINGS['debug'] = False
SETTINGS['equalize'] = True
SETTINGS['undistort'] = False
SETTINGS['enhance1'] = False
SETTINGS['enhance2'] = True
SETTINGS['e2_toZero_thresh'] = 33
SETTINGS['e2_trunc_thresh'] = 220
SETTINGS['filtering'] = False
SETTINGS['filtering_glint'] = True
SETTINGS['method'] = "threshold"
SETTINGS['autothreshold'] = True
SETTINGS['resize'] = True
SETTINGS['flip'] = True
SETTINGS['mode'] = "live"
SETTINGS['looplength'] = 100
SETTINGS['brightness'] = 0.98
SETTINGS['minSpotBrightness'] = 180
SETTINGS['gammaAdjust'] = 3.85
SETTINGS['inpaintRadius'] = 2
SETTINGS['claheClipLimit'] = 1.9
SETTINGS['grayBlurRadius'] = 5
SETTINGS['currentFile'] = "rec.avi"

SETTINGS['yOffTop'] = -120
SETTINGS['yOffBot'] = 70
SETTINGS['xOffLeft'] = -70
SETTINGS['xOffRight'] = 190

#SETTINGS['modes'] = ["live", "file", "loop"]

FRMPROV = None

'''Incremental Logging Dictionary'''
LOGS = {0: "init"}

'''Old settings'''
DEBUG = False
SHOW_ALL = True
EQUALIZE = False
UNDISTORT = False
ENHANCE1 = False
ENHANCE2 = True
FILTERING = False
FILTERING_GLINT = True
# METHOD = "flood"
METHOD = "threshold"
AUTOTHRESHOLD = True

def logAppend(message):
    if(len(LOGS) < 1000):
        LOGS[(time.time() * 1000)] = message

def logClear():
    LOGS = {}

