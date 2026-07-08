import json
import tkinter as tk
from videoServer import VideoServer
from controlServer import ControlServer

import sys
sys.path.append('./server')

from control import Control

def refresh_display():
    video_server.refresh_gui()
    root.after(10, refresh_display)



with open('settings.json') as f:
    settings = json.load(f)


root = tk.Tk()
root.title("W. H. I. L. E. T. R. U. E.")

video_frame = tk.Frame(root, width=settings["IMAGE_WIDTH"], height=settings["IMAGE_HEIGHT"])
video_frame.pack_propagate(False)
video_frame.pack(side="left")

image_label = tk.Label(video_frame, text="Waiting for connection...", font=("Arial", 24))
image_label.pack(fill="both", expand=True)

print("Starting video server")
video_server = VideoServer(
    image_label,
    host=settings["LISTEN_IP"],
    port=settings["VIDEO_PORT"],
    width=settings["IMAGE_WIDTH"],
    height=settings["IMAGE_HEIGHT"],
    channels=settings["IMAGE_CHANNELS"]
)

refresh_display()

print("Starting control server")
controlC = ControlServer(settings["LISTEN_IP"], settings["CONTROL_PORT"])
controlC.start(Control, settings["THREAD_SLEEP"])


print("Starting mainloop")
root.mainloop()