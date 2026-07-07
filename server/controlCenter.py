import json
import tkinter as tk
from videoServer import VideoServer

with open('settings.json') as f:
    settings = json.load(f)



root = tk.Tk()
root.title("W. H. I. L. E. T. R. U. E.")

video_frame = tk.Frame(root, width=settings["IMAGE_WIDTH"], height=settings["IMAGE_HEIGHT"])
video_frame.pack_propagate(False)
video_frame.pack(side="left")

image_label = tk.Label(video_frame, text="Waiting for connection...", font=("Arial", 24))
image_label.pack(fill="both", expand=True)

# Initialize video server
video_server = VideoServer(
    image_label,
    host=settings["LISTEN_IP"],
    port=settings["VIDEO_PORT"],
    width=settings["IMAGE_WIDTH"],
    height=settings["IMAGE_HEIGHT"],
    channels=settings["IMAGE_CHANNELS"]
)

def refresh_display():
    video_server.refresh_gui()
    root.after(10, refresh_display)

def on_closing():
    video_server.close_window()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
refresh_display()

root.mainloop()