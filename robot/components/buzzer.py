import time
from threading import Thread
import json
from control import Control

import RPi.GPIO as GPIO


class Buzzer():
    def __init__(self, volume = 50):
        self.pin = 16
        self.volume = volume

        self.running = False
        self.thread = None
        self.current_song = None
        self.current_index = None
        
        with open('songs.json') as f:
            self.songs = json.load(f)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.buzz = GPIO.PWM(self.pin, 440) 

    def play(self, song):
        self.current_song = self.songs.get(song)
        print(self.current_song)
        self.current_index = 0
    
    def silence(self):
        self.current_song = None
        self.current_index = None

    def start(self, Control, thread_sleep=0.1):    
        self.running = True
        self.thread = Thread(target=self.control_thread, args=(Control, thread_sleep))
        self.thread.start()

    def control_thread(self, Control, thread_sleep):
        while self.running:
            if self.current_song is not None and self.current_index is not None:
                note = self.current_song[self.current_index]
                frequency = note[0]
                duration = note[1]
                self.buzz.ChangeFrequency(frequency)
                self.buzz.start(self.volume)
                t0 = time.time_ns()
                while (time.time_ns() - t0) < duration * 1000000000:
                    pass
                self.buzz.stop()
                if self.current_index is not None:
                    self.current_index += 1
                if self.current_index >= len(self.current_song):
                    self.current_song = None
                    self.current_index = None
            else:
                time.sleep(thread_sleep)

    def __del__(self):
        self.running = False
        if self.thread:
            self.thread.join()
        GPIO.cleanup()
