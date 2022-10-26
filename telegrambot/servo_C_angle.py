# Import libraries
import RPi.GPIO as GPIO
import time

# Set GPIO numbering mode
GPIO.setmode(GPIO.BOARD)

# Set pin 11 as an output, and define as servo1 as PWM pin
GPIO.setup(40,GPIO.OUT)
servo1 = GPIO.PWM(40,50) # pin 11 for servo1, pulse 50Hz

# Start PWM running, with value of 0 (pulse off)
##Horizontal Servo BEgining##
GPIO.setup(38,GPIO.OUT)
servo2 = GPIO.PWM(38,50) 
##End of horizontal


