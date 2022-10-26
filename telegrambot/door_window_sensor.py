import RPi.GPIO as gpio
from time import sleep
global cond
cond=False
def setup():
    gpio.setmode(gpio.BCM)
    gpio.setwarnings(False)
    hallpin = 27
    gpio.setup(hallpin, gpio.IN)
    
def magnetic_sensor():
    i = False

    for x in range(5):
        if((gpio.input(27) == False) and i ):
            #gpio.output(ledpin, True)
            print("Magnetic field detected: Intruder detected")
            sleep(2)
            i = False
            cond= True
        elif((gpio.input(27) == True) and i==False):
            #gpio.output(ledpin, False)
            print("Magnetic field not detected")
            i = True
            cond=False
            sleep(2)


