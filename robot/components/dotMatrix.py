import RPi.GPIO as GPIO
import time
import json

class DotMatrix:

    def __init__(self):
        GPIO.setmode(GPIO.BCM)

        self.running = False
        self.SCLK = 14
        self.DIO  = 4
        self.thread = ""

        with open('dot_matrices.json') as f:
            self.images = json.load(f)
      
        GPIO.setwarnings(True)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.SCLK,GPIO.OUT)
        GPIO.setup(self.DIO,GPIO.OUT)

    def nop(self):
        time.sleep(0.00003)
        
    def start(self):
        GPIO.output(self.SCLK,0)
        self.nop()
        GPIO.output(self.SCLK,1)
        self.nop()
        GPIO.output(self.DIO,1)
        self.nop()
        GPIO.output(self.DIO,0)
        self.nop()
        
    def matrix_clear(self):
        self.matrix_display([0]*16)
        
    def send_data(self, data):
        for i in range(0,8):
            GPIO.output(self.SCLK,0)
            self.nop()
            if data & 0x01:
                GPIO.output(self.DIO,1)
            else:
                GPIO.output(self.DIO,0)
            self.nop()
            GPIO.output(self.SCLK,1)
            self.nop()
            data >>= 1
            GPIO.output(self.SCLK,0)
        
    def end(self):
        GPIO.output(self.SCLK,0)
        self.nop()
        GPIO.output(self.DIO,0)
        self.nop()
        GPIO.output(self.SCLK,1)
        self.nop()
        GPIO.output(self.DIO,1)
        self.nop()
        
    def matrix_display(self, matrix_value):
        self.start()
        self.send_data(0xc0)
        
        for i in range(0,16):
            self.send_data(matrix_value[i])
            
        self.end()
    
    def show(self, name):
        self.matrix_display(self.images[name])

    def __del__(self):
        if self.running:
            self.running = False
            self.thread.join()
        self.matrix_clear()
        GPIO.cleanup() 

if __name__ == "__main__":

    dot_matrix = DotMatrix()

    try:
        while True:
            for img in dot_matrix.images.keys() :
                print(img)
                dot_matrix.matrix_display(dot_matrix.images[img])
                time.sleep(2)

    except KeyboardInterrupt:
        #GPIO.cleanup()
        pass