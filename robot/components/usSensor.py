import time
from threading import Thread
from control import Control

import RPi.GPIO as GPIO

class USSensor:

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.US_TRIGGER = 9
        self.US_ECHO = 8

        GPIO.setup(self.US_TRIGGER, GPIO.OUT)
        GPIO.setup(self.US_ECHO, GPIO.IN)
        
        self.running = True
        self.thread = None

    def start(self, Control, thread_sleep=0.1):
        self.thread = Thread(target = self.control_thread, args = (Control, thread_sleep))
        self.thread.start()

    def control_thread(self, Control, thread_sleep=0.1):
        while self.running:
            if Control.us_measuring:
                Control.us_measurement = self.distance()
            time.sleep(thread_sleep)

    def distance(self):
        # 10us is the trigger signal
        GPIO.output(self.US_TRIGGER, GPIO.HIGH)
        time.sleep(0.00001)  #10us
        GPIO.output(self.US_TRIGGER, GPIO.LOW)
        while not GPIO.input(self.US_ECHO):
            pass
        t1 = time.monotonic_ms()
        while GPIO.input(self.US_ECHO):
            pass
        t2 = time.monotonic_ms()
        return ((t2 - t1) * 340 / 20)
    
    def __del__(self):
        self.running = False
        try:
            self.thread.join()
        except:
            pass