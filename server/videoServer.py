import shutil
import subprocess
import threading
import json
import time

import torch
import torchvision
import image_processing
import cv2

import numpy as np
from PIL import Image, ImageTk
import tkinter as tk

class VideoServer:
    def __init__(self, image_label, host, port, width, height, channels, Control):
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
        self.edge_detector = image_processing.EdgeDetector(image_processing.ElongatedMaskKernel(device=self.device))
        self.image_label = image_label
        self.host = host
        self.port = port
        self.width = width
        self.height = height
        self.channels = channels
        self.Control = Control
        self.frame_size = width * height * channels

        self.latest = {"raw": None, "frame": None, "count": 0, "shown": 0, "error": None, "fps": 0.0, "last_fps_time": time.perf_counter(), "last_fps_count": 0,}
        self.stop_event = threading.Event()
        self.decoder = self.start_decoder()

        print(self.device)
        threading.Thread(target=self.receiver_loop, daemon=True).start()
        threading.Thread(target=self.processing_loop, daemon=True).start()

    def preprocess_display(self, frame):
        image = torchvision.transforms.ToTensor()(frame)[:3].to(device=self.device)
        with torch.no_grad():
            edges = self.edge_detector.detect(image)#.to(self.device)

        edges_array = edges.squeeze().detach().cpu().numpy()
        edges_array = np.abs(edges_array)
        if edges_array.max() <= 1.0:
            edges_array = edges_array * 255.0
        edges_array = np.clip(edges_array, 0, 255).astype(np.uint8)
        # return frame
        return edges_array


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
                frame = np.frombuffer(payload, dtype=np.uint8).reshape((self.height, self.width, 3))
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
            if self.Control.preprocess == 1:
                processed = self.preprocess_display(frame)
                self.latest["frame"] = processed
            elif self.Control.preprocess == 2:
                canny_processed = cv2.Canny(frame, 100, 200)
                self.latest["frame"] = canny_processed
            else:
                self.latest["frame"] = frame
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

        # For displaying curent FPS
        now = time.perf_counter()
        elapsed = now - self.latest["last_fps_time"]

        if elapsed >= 1.0:
            frames = self.latest["shown"] - self.latest["last_fps_count"]
            self.latest["fps"] = frames / elapsed
            self.latest["last_fps_time"] = now
            self.latest["last_fps_count"] = self.latest["shown"]
            print(f"{self.latest['fps']:.1f} FPS")