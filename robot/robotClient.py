import json
from videoClient import VideoClient

with open('settings.json') as f:
    settings = json.load(f)


video_client = VideoClient(
    target_host=settings["HOST_IP"],
    port=settings["VIDEO_PORT"],
    width=settings["IMAGE_WIDTH"],
    height=settings["IMAGE_HEIGHT"],
    fps=settings["FPS"],
)

video_client.run()