import os
import sys
import RPi.GPIO as gpio
from mfrc522 import SimpleMFRC522
import time
CardRead = SimpleMFRC522()
 
load1 = 11
load2 = 12
load3 = 13
 
gpio.setmode(gpio.BOARD)
gpio.setwarnings(False)
gpio.setup(load1,gpio.OUT)
gpio.setup(load2,gpio.OUT)
gpio.setup(load3,gpio.OUT)
id=0
def card_read():
    print ('Card Scanning')
    print ('for Cancel Press ctrl+c')
 
    try:
        for index in range(3):
            global id
            id, text = CardRead.read()
            print(id)
            print(text)
     
    except KeyboardInterrupt:
        gpio.cleanup()
