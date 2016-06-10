import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)

p = GPIO.PWM(21, 100)
p.start(30)
input('Press return to stop:')   # use raw_input for Python 2
p.stop()
GPIO.cleanup()