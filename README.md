# ImgProcInWignerRobot

A fork of [**WignerRobot**](https://github.com/<your-org>/WignerRobot) used to test the [`image-processing`](https://github.com/dcintlab/image-processing) edge-detection package on the live video feed of the robot.

WignerRobot is a client/server framework for remotely driving a Raspberry Pi–based robot car from a PC: the PC runs a Tkinter **control center** that renders the robot's video stream and sends control commands, while the Raspberry Pi runs a **robot client** that drives the motors/servos/sensors and streams its camera feed back over UDP via `ffmpeg`.

This fork keeps the robot side untouched and modifies only the **server's video pipeline**, so that each incoming video frame can optionally be run through:

- the GPU-accelerated `EdgeDetector` (elongated-mask kernel) from the `image-processing` package, or
- OpenCV's classic Canny edge detector,

as a live, switchable overlay on top of the normal camera view — a quick way to sanity-check the edge-detection package on real, noisy, moving camera footage instead of static test images.

## What's different from WignerRobot

| Area | Change |
|---|---|
| `server/videoServer.py` | `VideoServer` now takes the shared `Control` object, runs each decoded frame through a selectable preprocessing step, and tracks/prints a live FPS counter |
| `server/keybindings.py` | New key (`E`) cycles through the display modes |
| `server/control.py` | New `preprocess` field (`0`/`1`/`2`) on the shared control state |
| `server/controlCenter.py` | Passes `Control` into `VideoServer` so key presses can change the display mode live |
| `settings.json` | Example `HOST_IP`/`FPS` values used for this test setup |

The robot-side code (`robot/`), `songs.json`, and `dot_matrices.json` are unchanged from the upstream WignerRobot repository — see its README for driving controls, hardware wiring, and general setup.

## Display Modes

Press **`E`** in the control-center window to cycle through:

| Mode | Value | Behaviour |
|---|---|---|
| Raw | `0` (default) | Shows the camera feed unmodified |
| `image-processing` EdgeDetector | `1` | Runs the frame through `image_processing.EdgeDetector` using an `ElongatedMaskKernel`, on GPU (CUDA/MPS) if available, otherwise CPU |
| OpenCV Canny | `2` | Runs `cv2.Canny(frame, 100, 200)` on the frame for a classic-edge-detection comparison |

The current FPS is printed to the console once per second so the cost of each mode can be compared directly.

## Requirements

This fork adds the following on top of the base WignerRobot dependencies (**server/PC side only** — the robot side is unaffected):

- `torch` >= 2.4
- `torchvision` >= 0.19
- `opencv-python` (regular, non-headless build, since it's used on the GUI machine)
- the [`image-processing`](https://github.com/dcintlab/image-processing) package itself

These are **not** yet part of `environment.yml`, so install them manually after creating the base environment.

## Installation

```bash
git clone https://github.com/<your-org>/ImgProcInWignerRobot.git
cd ImgProcInWignerRobot
conda env create -f environment.yml
conda activate WignerRobot

# Additional dependencies for the edge-detection integration
pip install torch torchvision opencv-python

# Install the image-processing package (editable install from a local clone,
# or directly from git)
git clone https://github.com/dcintlab/image-processing.git ../image-processing
pip install -e ../image-processing
# or: pip install git+https://github.com/dcintlab/image-processing.git
```

> A CUDA-capable GPU (or Apple Silicon for MPS) is optional but recommended for mode `1` — `VideoServer` automatically falls back to CPU if neither is available.

## Configuration

Same `settings.json` as upstream WignerRobot, with two values adjusted for this test setup:

| Key | Value here | Notes |
|---|---|---|
| `HOST_IP` | example PC IP on the test network | update to your own PC's IP before running |
| `FPS` | `60` | raised from the upstream default of `30` to leave more headroom for measuring the overhead of each preprocessing mode |

All other keys (ports, image size, motor/servo limits, etc.) are unchanged — see the upstream WignerRobot README for the full reference table.

## Usage

**1. Start the control center on the PC:**

```bash
cd ImgProcInWignerRobot
python server/controlCenter.py
```

**2. Start the robot client on the Raspberry Pi (unchanged from upstream):**

```bash
cd ImgProcInWignerRobot
python robot/robotClient.py
```

**3. Drive as usual**, and press **`E`** at any time to cycle the video feed between raw / `image-processing` edges / OpenCV Canny edges. Watch the console for the live FPS reading in each mode.

For the full set of driving/servo/buzzer keybindings, see the upstream [WignerRobot README](https://github.com/<your-org>/WignerRobot).

## License

No license file is included in this repository. The bundled `image-processing` package it depends on is licensed under **GPL-3.0** — keep this in mind before redistributing this fork.
