
import mysql.connector
from datetime import datetime
import time
import RPi.GPIO as gpio
##Door Servo to be unlocked according to check_log
gpio.setmode(gpio.BOARD)
gpio.setup(18,gpio.OUT)
servo1 = gpio.PWM(18,50)

gpio.setup(37, gpio.OUT)

#Buzzer
gpio.setmode(gpio.BOARD)
gpio.setup(11, gpio.OUT)

#Database Functions
def introduce_guest(guest_RFID):
    db = mysql.connector.connect(host="localhost", user="admin", passwd="1234", database="security")
    mycursor = db.cursor()
    mycursor.execute("INSERT INTO guests (RFID) VALUES (%s)", (guest_RFID,))
    db.commit()




def introduce_resident(re_name, re_mail, re_RFID):
    db = mysql.connector.connect(host="localhost", user="admin", passwd="1234", database="security")
    mycursor = db.cursor()
    mycursor.execute("INSERT INTO residents (name, mail, RFID) VALUES (%s, %s, %s)", (re_name, re_mail, re_RFID))
    db.commit()


#CHECK and LOG,
def check_log(activity, entered_RFID=None):
    servo1.start(0)
    
    db = mysql.connector.connect(host="localhost", user="admin", passwd="1234", database="security")
    mycursor = db.cursor(dictionary=True)

    # Checking Guests upon a RFID code
    mycursor.execute("SELECT * FROM guests WHERE RFID= '%s'" % (entered_RFID))
    mycursor.fetchall()
    if mycursor.rowcount == 1:
        
        #OPEN THE DOOR CODE SEGMENT#
        gpio.output(37,True)
                
        servo1.ChangeDutyCycle(2+(90/18))
        time.sleep(0.5) 
        servo1.ChangeDutyCycle(0)
        
        servo1.start(0)
        time.sleep(1)    
        servo1.ChangeDutyCycle(2+(0/18))
        time.sleep(0.5)
        servo1.ChangeDutyCycle(0)
    
        gpio.output(37,False)   
        
        #END OF OPEN THE DOOR CODE SEGMENT

        mycursor.execute("SELECT * FROM guests WHERE RFID= '%s'" % (entered_RFID))
        guest_info = mycursor.fetchone()
        guestRFID = guest_info["RFID"]
        print("correct RFID")
        print("the RFID info retrieved from table " + guestRFID)

        #Log for guests entry
        mycursor.execute("INSERT INTO log (name, activity, date) VALUES(%s, %s, %s)", ("Guest whose RFID is "+ entered_RFID,activity , datetime.now()))
        db.commit()
        return "guest_okay", "no_name"


    mycursor.execute("SELECT * FROM residents WHERE RFID= '%s'" % (entered_RFID))
    mycursor.fetchall()
    if mycursor.rowcount == 1:
        
        #OPEN THE DOOR CODE SEGMENT#
        gpio.output(37,True)
                
        servo1.ChangeDutyCycle(2+(90/18))
        time.sleep(0.5) 
        servo1.ChangeDutyCycle(0)
        
        servo1.start(0)
        time.sleep(1)    
        servo1.ChangeDutyCycle(2+(0/18))
        time.sleep(0.5)
        servo1.ChangeDutyCycle(0)
    
        gpio.output(37,False)   
        
        #END OF OPEN THE DOOR CODE SEGMENT

        mycursor.execute("SELECT * FROM residents WHERE RFID= '%s'" % (entered_RFID))
        resident_info = mycursor.fetchone()
        email= resident_info["mail"]
        print("you are a resident")
        print("the mail info retrieved from table " + email)
        resi_name=resident_info["name"]
        #Log for residents entry
        mycursor.execute("INSERT INTO log (name, activity, date) VALUES(%s, %s, %s)", (resi_name, activity , datetime.now()))
        db.commit()
        return "resident_okay", resi_name

    if entered_RFID != None:
        ##BUZZER CODE SEGMENT##
        Buzz = gpio.PWM(11, 700)
        Buzz.start(40)
        time.sleep(3)
        Buzz.stop()
        ##END OF BUZZER CODE SEGMENT##
        
        activity = activity + " attempt"
        mycursor.execute("INSERT INTO log (name,activity ,date) VALUES(%s, %s, %s)", ("Failed by RFID: " + entered_RFID,activity , datetime.now()))
        db.commit()
        return "wrong_rfid", entered_RFID

    elif entered_RFID == None:
        activity= "entry attempt"
        mycursor.execute("INSERT INTO log (name, activity ,date) VALUES(%s, %s, %s)", ("Failed face recognition attempt.", activity, datetime.now()))
        db.commit()
        return " ", " "



def motion_log(sensor):
    db = mysql.connector.connect(host="localhost", user="admin", passwd="1234", database="security")
    mycursor = db.cursor(dictionary=True)
    activity = "entry attempt"
    if sensor =="door":
        mycursor.execute("INSERT INTO log (name, activity ,date) VALUES(%s, %s, %s)", ("Motion detected by door sensor!", activity  , datetime.now()))
        db.commit()
        return
    elif sensor =="window":
        mycursor.execute("INSERT INTO log (name, activity ,date) VALUES(%s, %s, %s)",("Motion detected by window sensor!",activity , datetime.now()))
        db.commit()
        return
    elif sensor =="motion":
        mycursor.execute("INSERT INTO log (name, activity ,date) VALUES(%s, %s, %s)",("Motion detected by motion sensor!", activity, datetime.now()))
        db.commit()
        return



def get_log(condition=None, lastfive=False): #Returns string
    db = mysql.connector.connect(host="localhost", user="admin", passwd="1234", database="security")
    mycursor = db.cursor(dictionary=True)
    string = ""
    flag=1


    if condition==None:
        mycursor.execute("SELECT * FROM log")
        mycursor.fetchall()
        if mycursor.rowcount >= 1:
            mycursor.execute("SELECT * FROM log")
            list=mycursor.fetchall()
            if lastfive:
                list = list[-5:]
            for x in list:
                string += str(flag) + ") " + x["name"] + ", " + x["activity"] + ", " + str(x["date"].strftime("%d/%m/%y, %H:%M:%S")) + "\n\n"

                flag+=1

            return string
        else:
            string="There is no any activity log"
            return string



    elif condition=="fail":
        mycursor.execute("SELECT * FROM log WHERE activity= '%s'" % ("entry attempt"))
        mycursor.fetchall()
        if mycursor.rowcount >= 1:
            mycursor.execute("SELECT * FROM log WHERE activity= '%s'" % ("entry attempt"))
            list = mycursor.fetchall()
            if lastfive:
                list = list[-5:]
            for x in list:
                string += str(flag) + ") " + x["name"] + ", " + x["activity"] + ", " + str(
                    x["date"].strftime("%d/%m/%y, %H:%M:%S")) + "\n\n"

                flag += 1
            return string

        else:
            string="There is no any detected failed attempt"
            return string

def get_residents():
    db = mysql.connector.connect(host="localhost", user="admin", passwd="1234", database="security")
    mycursor = db.cursor(dictionary=True)
    string = ""
    flag = 1
    mycursor.execute("SELECT * FROM residents")
    mycursor.fetchall()
    if mycursor.rowcount >= 1:
        mycursor.execute("SELECT * FROM residents")
        for x in mycursor.fetchall():
            hidden_rfid= x["RFID"][0:len(x["RFID"])-4] + "****"
            string += str(flag) + ") " + x["name"] + ", " + x["mail"] + ", " + hidden_rfid+"\n\n"
            flag += 1
        return string

    else:
        string = "There is no any residents in the database."
        return string


def get_guests():
    db = mysql.connector.connect(host="localhost", user="admin", passwd="1234", database="security")
    mycursor = db.cursor(dictionary=True)
    string = ""
    flag = 1
    mycursor.execute("SELECT * FROM guests")
    mycursor.fetchall()
    if mycursor.rowcount >= 1:
        mycursor.execute("SELECT * FROM guests")
        for x in mycursor.fetchall():
            hidden_rfid= x["RFID"][0:len(x["RFID"])-4] + "****"
            string += str(flag) + ") " + hidden_rfid+"\n\n"
            flag += 1
        return string

    else:
        string = "There is no any RFID card assigned for a guest in the database."
        return string


