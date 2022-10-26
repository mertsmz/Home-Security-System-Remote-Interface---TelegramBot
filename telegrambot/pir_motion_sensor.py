from gpiozero import MotionSensor
pir=MotionSensor(4)
def motion():
         global ind

         pir.wait_for_motion()
         print(1)
         print("Motion Detected")
         print(2)
         ind =1
         pir.wait_for_no_motion()
         print(3)
         print("Motion Stopped")
         ind =0
                   


