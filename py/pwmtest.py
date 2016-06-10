from __future__ import division
import signal
import socket
import time
import string
import sys
import RPIO.PWM as PWM
import time
import math
import threading
import logging
from array import *
import select
import os
import struct

#--------------------------------------------------
# set up PWM pulse increment to 1us
#--------------------------------------------------
PWM.setup(1)

#--------------------------------------------------
# set up DMA channel one (there are 14 available) with
# 3ms subcycle time
#--------------------------------------------------
PWM.init_channel(4, 3000)

#--------------------------------------------------
# Assign four BCM GPIO port outputs to the channel
# each with their own pulses - 1ms, 1.25ms, 1.5ms & 2ms
#--------------------------------------------------
PWM.add_channel_pulse(1, 21, 0, 1250)

#------------------------------------------------------
# Sleep so I can check the oscilloscope
#------------------------------------------------------
time.sleep(10)

#------------------------------------------------------
# Flip thepulses round to show it works
#------------------------------------------------------
PWM.add_channel_pulse(1, 21, 0, 1500)



#------------------------------------------------------
# Pause for thought again.
#------------------------------------------------------
time.sleep(10)


#------------------------------------------------------
# Clear each GPIO from the channel one by one
#------------------------------------------------------
PWM.clear_channel_gpio(1, 21)
time.sleep(1)



#------------------------------------------------------
# Do the final cleanup
#------------------------------------------------------
PWM.clear_channel(1)
PWM.cleanup()