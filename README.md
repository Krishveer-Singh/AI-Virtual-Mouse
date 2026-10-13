# AI Virtual Mouse Using Hand Recognition

A touch-free virtual mouse built with Python, OpenCV, MediaPipe, and PyAutoGUI. It uses hand landmarks and gestures to control mouse actions through a camera.

## Features

- Real-time hand tracking using MediaPipe
- Cursor movement using hand gestures
- Left-click and double-click
- Right-click
- Scroll up and scroll down
- Drag-and-drop
- Zoom in and zoom out (where supported by the target application)
- Separate code versions for Windows and macOS

## Technologies Used

- Python
- OpenCV
- MediaPipe
- PyAutoGUI
- NumPy

## Project Files

- `main.py` — Main project version
- `main1.py` — Alternate/test version
- `AI_Virtual_Mouse_macOS.py` — macOS version
- `AI_Virtual_Mouse_macOS_updated.py` — Updated macOS version
- `hand_landmarker.task` — MediaPipe hand landmark model

## Requirements

- Python version compatible with the installed MediaPipe and OpenCV packages
- A working webcam
- Camera and accessibility permissions on macOS

## Setup

Create and activate a virtual environment.

### Windows (PowerShell)

python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install opencv-python mediapipe pyautogui


### macOS

python3.12 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install opencv-python mediapipe pyautogui

## Run the Project

### Windows

python main.py

### macOS

python AI_Virtual_Mouse_macOS_updated.py

Make sure `hand_landmarker.task` is in the location expected by the selected Python script.

## Notes

- The `venv` folder should not be uploaded to GitHub. Each operating system needs its own environment.
- On macOS, allow camera access and the required Accessibility permissions for mouse control.
- Gesture recognition can be affected by lighting, camera quality, and background conditions.
- The project is a prototype and may not work identically across all applications or computers.

## Author

Created as a learning project exploring computer vision and gesture-based human-computer interaction.