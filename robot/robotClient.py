import json
from threading import Thread
from videoClient import VideoClient
import sys

sys.path.append('./robot/components')
sys.path.append('./robot')

from buzzer import Buzzer
from motor import Motor
from servo import Servo
from usSensor import USSensor
from controlClient import ControlClient

from control import Control

with open('settings.json') as f:
    settings = json.load(f)

print("Starting video client")
video_client = VideoClient(
    target_host=settings["HOST_IP"],
    port=settings["VIDEO_PORT"],
    width=settings["IMAGE_WIDTH"],
    height=settings["IMAGE_HEIGHT"],
    fps=settings["FPS"],
)

video_thread = Thread(target=video_client.run)
video_thread.start()

print("Starting hardware components")
motor = Motor()
motor.start(Control, settings["THREAD_SLEEP"])
    
servo = Servo()
servo.start(Control, settings["THREAD_SLEEP"])

us_sensor = USSensor()
us_sensor.start(Control, settings["THREAD_SLEEP"])

print("Starting control client")
control_client = ControlClient(settings["HOST_IP"], settings["CONTROL_PORT"])
