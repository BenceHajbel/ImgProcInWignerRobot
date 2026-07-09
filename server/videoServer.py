import shutil
import subprocess
import threading
import json
import time

import numpy as np
from PIL import Image, ImageTk
import tkinter as tk

def preprocess_display(frame):
    return frame


class VideoServer:
    def __init__(self, image_label, host, port, width, height, channels):
        
        self.image_label = image_label
        self.host = host
        self.port = port
        self.width = width
        self.height = height
        self.channels = channels
        self.frame_size = width * height * channels

        self.latest = {"raw": None, "frame": None, "count": 0, "shown": 0, "error": None}
        self.stop_event = threading.Event()
        self.decoder = self.start_decoder()

        threading.Thread(target=self.receiver_loop, daemon=True).start()
        threading.Thread(target=self.processing_loop, daemon=True).start()

    @staticmethod
    def recv_exact(pipe, size):
        buffer = bytearray()
        while len(buffer) < size:
            chunk = pipe.read(size - len(buffer))
            if not chunk:
                raise ConnectionError("Stream closed")
            buffer.extend(chunk)
        return bytes(buffer)

    def drain_stderr(self, process):
        if process.stderr is None:
            return
        for line in process.stderr:
            text = line.decode("utf-8", "replace").rstrip()
            if text:
                print(f"[ffmpeg] {text}")

    def decode_command(self, ffmpeg):
        return [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-fflags",
            "nobuffer",
            "-flags",
            "low_delay",
            "-probesize",
            "32",
            "-analyzeduration",
            "0",
            "-i",
            f"udp://{self.host}:{self.port}?fifo_size=5000000&overrun_nonfatal=1",
            "-an",
            "-vf",
            f"scale={self.width}:{self.height}",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "pipe:1",
        ]

    def start_decoder(self):
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg is not available in this conda environment")

        process = subprocess.Popen(
            self.decode_command(ffmpeg),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if process.stdout is None:
            raise RuntimeError("Could not open ffmpeg stdout")
        threading.Thread(target=self.drain_stderr, args=(process,), daemon=True).start()
        return process

    def close_window(self):
        self.stop_event.set()
        try:
            self.decoder.terminate()
            self.decoder.wait(timeout=2)
        except OSError:
            pass
        except subprocess.TimeoutExpired:
            self.decoder.kill()
            self.decoder.wait()

    def receiver_loop(self):
        stdout = self.decoder.stdout
        try:
            while not self.stop_event.is_set():
                payload = self.recv_exact(stdout, self.frame_size)
                frame = np.frombuffer(payload, dtype=np.uint8).reshape((self.height, self.width, 3)).copy()
                self.latest["raw"] = frame
        except (ConnectionError, OSError):
            pass
        finally:
            if not self.stop_event.is_set():
                self.latest["error"] = "Decoder stopped (see console for ffmpeg errors)"
            try:
                self.decoder.terminate()
            except OSError:
                pass

    def processing_loop(self):
        while not self.stop_event.is_set():
            frame = self.latest["raw"]
            if frame is None:
                time.sleep(0.001)
                continue
            self.latest["raw"] = None
            processed = preprocess_display(frame)
            self.latest["frame"] = processed
            self.latest["count"] += 1

    def refresh_gui(self):
        if self.stop_event.is_set():
            return

        error = self.latest["error"]
        if error is not None:
            self.image_label.configure(image="", text=error, fg="#dddddd")
            self.image_label.image = None
            return

        if self.latest["count"] != self.latest["shown"]:
            self.latest["shown"] = self.latest["count"]
            photo = ImageTk.PhotoImage(image=Image.fromarray(self.latest["frame"]))
            self.image_label.configure(image=photo)
            self.image_label.image = photo