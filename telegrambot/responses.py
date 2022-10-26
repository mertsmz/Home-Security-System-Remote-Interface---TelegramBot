from datetime import datetime
import database_functions_for_telegram as dbfuncs

def sample_responses(input_text):
    user_message = str(input_text).lower()

    if user_message in("hello", "hi"):
        return "Hello to you too."

    if user_message in("who are you", "who are you?"):
        return "I am a bot to be used in this project."

    if user_message in("time"):
        now = datetime.now()
        date_time = now.strftime("%d/%m/%y, %H:%M:%S")
        return str(date_time)
    
    if user_message in ("info"):
        return "\tThis is an user interface designed to be used for the HESTIA Home Security Systems. If you have the product, please type /authenticate and log in with your default ID-Password that is written on the back of the main control box."


    return "I didn't understand what you typed."

