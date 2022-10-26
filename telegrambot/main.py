
from telegram.ext import *
import responses as R
import database_functions_for_telegram as dbfunc
from datetime import datetime
import Reader_2 as reader
import pir_motion_sensor as motion
import camera as cam
from picamera import PiCamera
#import door_window_sensor as doorwindow
from gpiozero import MotionSensor
##from servo_C_angle.py
import servo_C_angle as servo
import RPi.GPIO as GPIO
import time
import os
import mysql.connector
import RPi.GPIO as gpio
import os.path
from pathlib import Path


API_KEY="YOUR_BOT'S_CHAT_ID"
print("Bot started...")
bot = ExtBot(API_KEY)

chatidforphoto=0
global ss_send
ss_send=False
global petss_send
petss_send=False
global cutss_send
cutss_send=False
chat_id_authenticated=[]
global time_started
time_started=0
global time_started_pet
time_started_pet=0
global time_started_crowd
time_started_crowd=0
global time_started_cut
time_started_cut=0

def start_command(update, context):
    ###For job queue
    context.job_queue.run_repeating(callback_10, interval=15, context=update.message.chat_id)
    context.job_queue.run_repeating(callback_5_rfid_read, interval=5, context=update.message.chat_id)
    context.job_queue.run_repeating(callback_5_unknown_photo, interval=5, context=update.message.chat_id)
    context.job_queue.run_repeating(callback_2_resident_face_detect, interval=2, context=update.message.chat_id)
    context.job_queue.run_repeating(callback_5_pet, interval=5, context=update.message.chat_id)
    context.job_queue.run_repeating(callback_5_crowd_photo, interval=5, context=update.message.chat_id)
    context.job_queue.run_repeating(callback_5_cut_tool, interval=5, context=update.message.chat_id)

    ###
    
    chat_id = update.message.chat_id
    global chatidforphoto
    chatidforphoto= chat_id
    bot.send_message(chat_id, "Type something to get started")

##AUTHENTICATION
DEFAULT_ID_PASS = range(1)
def authenticate_command(update, context):
    chat_id = update.message.chat_id
    global chat_id_authenticated
    bot.send_message(chat_id,'Please enter the default ID and Password in "ID:PASSWORD" format to authenticate your mobile device.' )
    return DEFAULT_ID_PASS


def got_default_id_pass(update, context):
    chat_id = update.message.chat_id
    def_id_pass = update.message.text
    if def_id_pass.lower()=="hestia:ee494":
        chat_id_authenticated.append(chat_id)
        bot.send_message(chat_id, "Authentication is successful. You can type /help to access options.")
    else:
        bot.send_message(chat_id, "Wrong ID or Password, authentication is failed!")
    return ConversationHandler.END
##



def help_command(update, context):
    chat_id = update.message.chat_id
    if chat_id in chat_id_authenticated:
        bot.send_message(chat_id,'1) Add a resident to the database.\1\n2) Add a guest to the database.\2\n3) Show all logs.\3\n4) Show last 5 logs.\4\n5) Show residents.\5\n6) Show guest RFID\'s.\6\n7) Change camera angle.\7\nTo open door type \opendoor.\n\nType the number of operation you want to perform with slash "/". ')
    else:
        bot.send_message(chat_id, "You are not authenticated to use this interface! If you have the HESTIA Home Security System, you can authenticate your device by typing /authenticate.")

def handle_message(update, context):
    text = str(update.message.text).lower()
    response = R.sample_responses(text)

    update.message.reply_text(response)




# ---------- defining states ---------
NAME, MAIL, RFID = range(3)


def add_resident_command(update, context):
    chat_id = update.message.chat_id
    bot.send_message(chat_id, "Hello, you are in introducing resident process! Please enter a name or you can type /cancel to end the process.")
    return NAME


def got_name(update, context):
    chat_id = update.message.chat_id
    name = update.message.text
    context.user_data["name"] = name
    bot.send_message(chat_id, f"Please enter a mail adress belongs to {name}")
    resident_info_file = open("/home/pi/Desktop/FINAL_DEMO/tkinter/resident_info.txt","w+")
    resident_info_file.write(name+"\nA\nA\nA")
    resident_info_file.close()
    return MAIL


def got_mail(update, context):
    chat_id = update.message.chat_id
    re_mail = update.message.text
    re_name = context.user_data["name"]
    context.user_data["mail"] = re_mail
    bot.send_message(chat_id, f"Please hold the RFID you want to assign for {re_name}.")
    reader.card_read()
    re_RFID = reader.id
    context.user_data["rfid"] = re_RFID
    re_name = context.user_data["name"]
    re_mail = context.user_data["mail"]
    hidden_rfid = str(re_RFID)[0:len(str(re_RFID))-4] + "****"
    context.user_data["hidden_rfid"] = hidden_rfid

    db = mysql.connector.connect(host="localhost", user="admin", passwd="1234", database="security")
    cursor_re = db.cursor(dictionary=True)
    cursor_re.execute("SELECT * FROM residents WHERE RFID= '%s'" % (re_RFID))
    cursor_re.fetchall()
    re_num = cursor_re.rowcount

    cursor_guest = db.cursor(dictionary=True)
    cursor_guest.execute("SELECT * FROM guests WHERE RFID= '%s'" % (re_RFID))
    cursor_guest.fetchall()
    guest_num = cursor_guest.rowcount

    if re_num < 1 and guest_num < 1:
        bot.send_message(chat_id,
        f"Please type /next when you get in front of the camera to initate face introduction process!")
        return RFID
    else:
        bot.send_message(chat_id, f"The RFID card whose code {hidden_rfid} already exists! Please start the process from the beginning by typing /1 if you want.")
        return ConversationHandler.END



    ##End of checking if RFID exists
    

def got_rfid(update, context):
    chat_id = update.message.chat_id
    command = update.message.text
    context.user_data["chat_id"] = chat_id
    re_name = context.user_data["name"]
    if command == "/next":
        bot.send_message(chat_id,"After 10 seconds the face introduction process will begin.")
        time.sleep(10)
        Buzz = gpio.PWM(11, 700)
        Buzz.start(40)
        time.sleep(1.5)
        Buzz.stop()
        resident_info_file = open("/home/pi/Desktop/FINAL_DEMO/tkinter/resident_info.txt","a+")
        resident_info_file.write("\nA")
        resident_info_file.close()
    
        bot.send_message(chat_id,"Face introduction process has begun. Please stay in the frame!")

        image_path = "/home/pi/Desktop/FINAL_DEMO/Face_Recognition/dataset/"+re_name+"/"
        image_file = image_path + "image_0.jpg"
        print(image_path)
        print(image_file)
        while not os.path.isdir(image_path):#directory oluşmasını beklemek için
            continue
        # file exists
        num=0
        image_name= "image_0.jpg"
        file_list = []
        while num<5:
            file_list = os.listdir(image_path)
            time.sleep(2)
            if image_name in file_list:
                print("image is exist now")
                context.bot.send_photo(chat_id, photo=open(image_path+image_name, 'rb'), caption="Taken image ("+ str(num)+").")
                num = num+1
                image_name = "image_" + str(num) + ".jpg"
            else:
                continue
        

        re_name = context.user_data["name"]
        re_mail = context.user_data["mail"]
        hidden_rfid = context.user_data["hidden_rfid"]
        bot.send_message(chat_id,f"Your face data is obtained. The resident whose name is {re_name}, mail is {re_mail} and RFID is {hidden_rfid} is added to database successfully!")
        re_name = context.user_data["name"]
        re_mail = context.user_data["mail"]
        re_RFID = context.user_data["rfid"]
        dbfunc.introduce_resident(re_name, re_mail, re_RFID)

        return ConversationHandler.END
    elif command =="/cancel": #process cancel
        return ConversationHandler.END
    else:
        return RFID


def cancel(update, context):
    chat_id = update.message.chat_id
    bot.send_message(chat_id, "Process cancelled!")
    return ConversationHandler.END



def add_guest_command(update, context):
    chat_id = update.message.chat_id
    bot.send_message(chat_id, "Hold a RFID to assign it for guests.")
    reader.card_read()
    guest_rfid = reader.id
    
    hidden_rfid = str(guest_rfid)[0:len(str(guest_rfid))-4] + "****"
    
    #Checking if RFID already exists
    db = mysql.connector.connect(host="localhost", user="admin", passwd="1234", database="security")
    cursor_re = db.cursor(dictionary=True)
    cursor_re.execute("SELECT * FROM residents WHERE RFID= '%s'" % (guest_rfid))
    cursor_re.fetchall()
    re_num = cursor_re.rowcount

    cursor_guest = db.cursor(dictionary=True)
    cursor_guest.execute("SELECT * FROM guests WHERE RFID= '%s'" % (guest_rfid))
    cursor_guest.fetchall()
    guest_num = cursor_guest.rowcount
    if re_num < 1 and guest_num < 1:
        dbfunc.introduce_guest(guest_rfid)
        bot.send_message(chat_id,f"Completed! RFID {hidden_rfid} was added to database for guests, successfully!")

    else:
        bot.send_message(chat_id, f"The RFID card whose code {hidden_rfid} already exists! Please start the process again by typing\n/2 if you want.")
    
    

####Show log functions
def show_all_log_command(update, context):
    chat_id = update.message.chat_id
    log_list = dbfunc.get_log()
    if log_list=="There is no any activity log":
        bot.send_message(chat_id,log_list + " by the date-time " + str(datetime.now().strftime("%d/%m/%y, %H:%M:%S")) +".")
    else:
        bot.send_message(chat_id, "\n//Name or Situation, Activity, Date-Time//\n--------------------------------------------------------------\n" + log_list)


def show_all_last5_log(update, context):
    chat_id = update.message.chat_id
    log_list = dbfunc.get_log(lastfive=True)
    if log_list == "There is no any activity log":
        bot.send_message(chat_id,
                         log_list + " by the date-time " + str(datetime.now().strftime("%d/%m/%y, %H:%M:%S")) + ".")
    else:
        bot.send_message(chat_id,
                         "//Name or Situation, Activity, Date-Time//\n--------------------------------------------------------------\n" + log_list)


def show_fail_attempt_log_command(update, context):
    chat_id = update.message.chat_id
    log_list = dbfunc.get_log(condition="fail")
    if log_list=="There is no any detected failed attempt":
        bot.send_message(chat_id,log_list + " by the date-time " + str(datetime.now().strftime("%d/%m/%y, %H:%M:%S")) +".")
    else:
        bot.send_message(chat_id, "//Name or Situation, Activity, Date-Time//\n--------------------------------------------------------------\n" + log_list)

def show_fail_attempt_last5_log_command(update, context):
    chat_id = update.message.chat_id
    log_list = dbfunc.get_log(condition="fail", lastfive=True)
    if log_list=="There is no any detected failed attempt":
        bot.send_message(chat_id,log_list + " by the date-time " + str(datetime.now().strftime("%d/%m/%y, %H:%M:%S")) +".")
    else:
        bot.send_message(chat_id, "//Name or Situation, Activity, Date-Time//\n--------------------------------------------------------------\n" + log_list)

####
def show_residents_command(update, context):
    chat_id = update.message.chat_id
    re_list = dbfunc.get_residents()
    if re_list=="There is no any residents in the database.":
        bot.send_message(chat_id, re_list)
    else:
        bot.send_message(chat_id, "//Name, Mail, RFID//\n--------------------------------------------------------------\n" + re_list)


def show_guests_command(update, context):
    chat_id = update.message.chat_id
    guest_list = dbfunc.get_guests()
    if guest_list  == "There is no any RFID card assigned for a guest in the database.":
        bot.send_message(chat_id, guest_list )
    else:
        bot.send_message(chat_id,
                         "//RFID//\n--------------------------------------------------------------\n" + guest_list )



def error(update, context):
    print(f"Update {update} caused error {context.error}")
    
    
DIRECTION = range(1)
def change_cam_command(update, context):
    chat_id = update.message.chat_id
    bot.send_message(chat_id, "Type the direction you want. (Right,Xmid,Left,Up,Ymid,Down)")
    return DIRECTION

def got_direction(update, context):    
    chat_id = update.message.chat_id
    direction = (update.message.text).lower()

    if direction == "left":
        
        (servo.servo1).start(0)
        
        GPIO.output(40,True)          
        (servo.servo1).ChangeDutyCycle(2+(135/18))        
        time.sleep(0.5)
        (servo.servo1).ChangeDutyCycle(0)
        GPIO.output(40,False) 
        bot.send_message(chat_id, "Cam has turned left.")
    
    elif direction == "right":
        (servo.servo1).start(0)
        
        GPIO.output(40,True)          
        (servo.servo1).ChangeDutyCycle(2+(45/18))        
        time.sleep(0.5)
        (servo.servo1).ChangeDutyCycle(0)
        GPIO.output(40,False)
        bot.send_message(chat_id, "Cam has turned right.")
        
    elif direction == "xmid":
        (servo.servo1).start(0)
        
        GPIO.output(40,True)          
        (servo.servo1).ChangeDutyCycle(2+(90/18))        
        time.sleep(0.5)
        (servo.servo1).ChangeDutyCycle(0)
        GPIO.output(40,False)
        bot.send_message(chat_id, "Cam is X-mid.")
    elif direction == "down":
        (servo.servo2).start(0)
        
        GPIO.output(38,True)          
        (servo.servo2).ChangeDutyCycle(2+(115/18))        
        time.sleep(0.5)
        (servo.servo2).ChangeDutyCycle(0)
        GPIO.output(38,False) 
        bot.send_message(chat_id, "Cam has turned up.")
        
    elif direction == "up":
        (servo.servo2).start(0)
        
        GPIO.output(38,True)          
        (servo.servo2).ChangeDutyCycle(2+(45/18))        
        time.sleep(0.5)
        (servo.servo2).ChangeDutyCycle(0)
        GPIO.output(38,False)
        bot.send_message(chat_id, "Cam has turned down.")
    
    elif direction == "ymid":
        (servo.servo2).start(0)
        
        GPIO.output(38,True)          
        (servo.servo2).ChangeDutyCycle(2+(90/18))        
        time.sleep(0.5)
        (servo.servo2).ChangeDutyCycle(0)
        GPIO.output(38,False)
        bot.send_message(chat_id, "Cam is Y-mid.")
        
    else:
        bot.send_message(chat_id, "You typed wrong input.")
    return ConversationHandler.END


def callback_10(context):
    print("callback10 running")
    chat_id = context.job.context
    #motion_condition= motion.motion()
    #pir=MotionSensor(4)
    (motion.pir).wait_for_motion()
    print(1)
    print("Motion Detected")
    
    ##CAM SERVO TURN
    (servo.servo1).start(0)
    
    GPIO.output(40,True)          
    (servo.servo1).ChangeDutyCycle(2+(135/18))        
    time.sleep(0.5)
    (servo.servo1).ChangeDutyCycle(0)
    
    ##
    
    ##CAMERA PHOTOSHOT
    cam.shot()
    file_name = "test.jpg"
    file_path = r"/home/pi/Desktop/telegrambot/" + file_name
    context.bot.send_photo(chat_id, photo=open(file_path, 'rb'), caption="Possible intrusion attempt at " + str(datetime.now().strftime("%d/%m/%y, %H:%M:%S"))+ "." )
    (motion.pir).wait_for_no_motion()
    print(3)
    print("Motion Stopped")
    ind =0

    ##For turning back
    (servo.servo1).start(0)                      
    time.sleep(1)
    print(4)    
    (servo.servo1).ChangeDutyCycle(2+(90/18))
    print(5)
    time.sleep(0.5)
    (servo.servo1).ChangeDutyCycle(0)
    print(7)
    GPIO.output(40,False)    

    #Clean things up at the end
    #(servo.servo1).stop()
    #GPIO.cleanup()
    #if photo_condition:
     #   context.bot.send_photo(chat_id, photo=open(file_path, 'rb'), caption="Possible intrusion attempt at " + str(datetime.now().strftime("%d/%m/%y, %H:%M:%S"))+ "." )

def callback_5_rfid_read(context):
    chat_id = context.job.context
 
    #context.bot.send_message(chat_id, text='this is 7 sec periodic message')
    reader.card_read()
    re_RFID = reader.id

    state, info = dbfunc.check_log("entry", entered_RFID=str(re_RFID))
    if not (chat_id in chat_id_authenticated):
        return
    if state == "guest_okay":
        context.bot.send_message(chat_id, text='A guest whose RFID is ' + str(re_RFID) + ' entered the house.')
    elif state == "resident_okay":
        context.bot.send_message(chat_id, text="Resident " + info + " entered the house.")
    elif state == "wrong_rfid":
        context.bot.send_message(chat_id, text="There has happened an entry attempt by the unauthorized RFID " + info + ".")

def callback_5_pet(context):
    global petss_send
    chat_id = context.job.context
    file_path = "/home/pi/Desktop/FINAL_DEMO/Pet_Detection/pet_img"
    file_list = os.listdir(file_path)
    print(file_list)
    global time_started_pet
    if time_started_pet ==0:
        time_started_pet=time.time()
    if time.time() > time_started_pet +7:
        time_started_pet=0
        petss_send=False
        if len(file_list) != 0:
            if not (chat_id in chat_id_authenticated):
                return
            context.bot.send_photo(chat_id, photo=open(file_path +"/" + file_list[0], 'rb'), caption="There is a pet in front of the door. If you want to let it in, you can open the door by typing '/opendoor'. (" + str(datetime.now().strftime("%d/%m/%y, %H:%M:%S")) + ")")
            petss_send = True
            for file in file_list:
                os.remove(file_path + "/" + file)
                
def callback_5_unknown_photo(context):
    global ss_send
    chat_id = context.job.context
    file_path = "/home/pi/Desktop/FINAL_DEMO/Face_Recognition/unknown"
    file_list = os.listdir(file_path)
    # Checking if the list is empty or not
    global time_started
    if time_started ==0:
        time_started=time.time()
    if time.time() > time_started +7:
        time_started=0
        ss_send=False
        if len(file_list) != 0:  # Folder boş değil case.
            if not (chat_id in chat_id_authenticated):
                return
            ss_send = True
            context.bot.send_photo(chat_id, photo=open(file_path +"/" + file_list[0], 'rb'), caption="There is someone in front of the door. If you want to let him in as guest, you can open the door by typing '/opendoor'. (" + str(datetime.now().strftime("%d/%m/%y, %H:%M:%S")) + ")")
            for file in file_list:
                os.remove(file_path + "/" + file)
        else:
            ss_send=False
            
def callback_5_crowd_photo(context):
    global crowdss_send
    chat_id = context.job.context
    file_path = "/home/pi/Desktop/FINAL_DEMO/Anomally_Crowded/anomally_img"
    file_list = os.listdir(file_path)
    global time_started_crowd
    if time_started_crowd ==0:
        time_started_crowd=time.time()
    if time.time() > time_started_crowd + 7:
        time_started_crowd=0
        crowdss_send=False
        if len(file_list) != 0:  # Folder boş değil case.
            if not (chat_id in chat_id_authenticated):
                return
            crowdss_send = True
            Buzz = gpio.PWM(11, 700)
            Buzz.start(40)
            time.sleep(3)
            Buzz.stop()
            #Logging crowd
            db = mysql.connector.connect(host="localhost", user="admin", passwd="1234", database="security")
            mycursor = db.cursor(dictionary=True)
            activity = "anomaly"
            mycursor.execute("INSERT INTO log (name, activity ,date) VALUES(%s, %s, %s)",("A Crowd is detected in front of the door!", activity, datetime.now()))  
            db.commit()
            context.bot.send_photo(chat_id, photo=open(file_path +"/" + file_list[0], 'rb'), caption="Warning! There is a group of people in front of your door!(" + str(datetime.now().strftime("%d/%m/%y, %H:%M:%S")) + ")")
            for file in file_list:
                os.remove(file_path + "/" + file)
        else:
            crowdss_send=False

def callback_5_cut_tool(context):
    global cutss_send
    chat_id = context.job.context
    file_path = "/home/pi/Desktop/FINAL_DEMO/Pet_Detection/cut_img"
    file_list = os.listdir(file_path)
    # Checking if the list is empty or not
    global time_started_cut
    if time_started_cut ==0:
        time_started_cut=time.time()
    if time.time() > time_started_cut + 7:
        time_started_cut=0
        cutss_send=False
        if len(file_list) != 0:
            if not (chat_id in chat_id_authenticated):
                return
            cutss_send = True
            Buzz = gpio.PWM(11, 700)
            Buzz.start(40)
            time.sleep(3)
            Buzz.stop()
            #Logging crowd
            db = mysql.connector.connect(host="localhost", user="admin", passwd="1234", database="security")
            mycursor = db.cursor(dictionary=True)
            activity = "anomaly"
            mycursor.execute("INSERT INTO log (name, activity ,date) VALUES(%s, %s, %s)",("A person with a cutting tool is detected!", activity, datetime.now()))  
            db.commit()
            context.bot.send_photo(chat_id, photo=open(file_path +"/" + file_list[0], 'rb'), caption="Warning! A person with a cutting tool in front of your door!(" + str(datetime.now().strftime("%d/%m/%y, %H:%M:%S")) + ")")
            for file in file_list:
                os.remove(file_path + "/" + file)
        else:
            cutss_send=False


def open_door(update, context):
    chat_id = update.message.chat_id
    (dbfunc.servo1)
    (dbfunc.servo1).ChangeDutyCycle(2+(90/18))
    time.sleep(0.5)
    (dbfunc.servo1).ChangeDutyCycle(0)
    (dbfunc.servo1).start(0)
    time.sleep(1)
    (dbfunc.servo1).ChangeDutyCycle(2+(0/18))
    time.sleep(0.5)
    (dbfunc.servo1).ChangeDutyCycle(0)

    global ss_send
    if ss_send==True:
        bot.send_message(chat_id, "The door opened for the last person that appeared in front of the door.")
        db = mysql.connector.connect(host="localhost", user="admin", passwd="1234", database="security")
        mycursor = db.cursor(dictionary=True)
        activity = "entry"
        mycursor.execute("INSERT INTO log (name, activity ,date) VALUES(%s, %s, %s)",("Guest welcomed by resident.", activity, datetime.now()))  
        db.commit()
        ss_send=False
        return
        
    global petss_send
    if petss_send ==True:
        bot.send_message(chat_id, "The door opened for the last pet that appeared in front of the door.")
        db = mysql.connector.connect(host="localhost", user="admin", passwd="1234", database="security")
        mycursor = db.cursor(dictionary=True)
        activity = "entry"
        mycursor.execute("INSERT INTO log (name, activity ,date) VALUES(%s, %s, %s)",("Pet welcomed by resident.", activity, datetime.now()))  
        db.commit()
        petss_send=False
        return

    if ss_send==False and petss_send ==False:
        bot.send_message(chat_id, "The door is open.")
        return
###########END OF LETTING GUEST IN##################
        

def callback_2_resident_face_detect(context):
    chat_id = context.job.context
    re_name_file = open("/home/pi/Desktop/FINAL_DEMO/telegrambot/resident_face_detect.txt","r")
    re_name_list = re_name_file.readlines()
    if len(re_name_list)>1:
        name = (re_name_list[0]).replace("\n", "")
        #clearing the the text file
        re_name_file = open("/home/pi/Desktop/FINAL_DEMO/telegrambot/resident_face_detect.txt","w+")
        re_name_file.close()
        print(name)
        if not (chat_id in chat_id_authenticated):
            return
        context.bot.send_message(chat_id, text="Resident " + name + " entered the house.")

    re_name_file.close()




def main():
    updater = Updater(API_KEY, use_context=True)
    dp = updater.dispatcher #Yazılan mesajı alabilmek için bu


    dp.add_handler(CommandHandler("start", start_command, pass_job_queue=True))
    dp.add_handler(CommandHandler("help", help_command))


    dp.add_handler(ConversationHandler(entry_points=[CommandHandler("1", add_resident_command)],states={NAME : [MessageHandler(Filters.text & (~ Filters.command), got_name)], MAIL: [MessageHandler(Filters.text & (~ Filters.command), got_mail)], RFID: [MessageHandler(Filters.text, got_rfid)]}, fallbacks = [MessageHandler(Filters.regex('cancel'), cancel)], allow_reentry= True))
    dp.add_handler(CommandHandler("2",add_guest_command))
    
    dp.add_handler(ConversationHandler(entry_points=[CommandHandler("7", change_cam_command)],states={DIRECTION: [MessageHandler(Filters.text& (~ Filters.command), got_direction)]}, fallbacks = [MessageHandler(Filters.regex('cancel'), cancel)], allow_reentry= True))
###### Authentication conservation
    dp.add_handler(ConversationHandler(entry_points=[CommandHandler("authenticate", authenticate_command)],
                                       states={DEFAULT_ID_PASS: [MessageHandler(Filters.text& (~ Filters.command), got_default_id_pass)]},
                                       fallbacks=[MessageHandler(Filters.regex('cancel'), cancel)], allow_reentry=True))

    dp.add_handler(CommandHandler("3",show_all_log_command))
    dp.add_handler(CommandHandler("4", show_all_last5_log))
    #dp.add_handler(CommandHandler("5", show_fail_attempt_log_command))
    #dp.add_handler(CommandHandler("6", show_fail_attempt_last5_log_command))
    dp.add_handler(CommandHandler("5", show_residents_command))
    dp.add_handler(CommandHandler("6", show_guests_command))
    dp.add_handler(CommandHandler("opendoor", open_door))

    dp.add_handler(MessageHandler(Filters.text, handle_message))

    dp.add_error_handler(error)
    
    updater.start_polling()


    
    updater.idle() 


if __name__ == '__main__':
    main()