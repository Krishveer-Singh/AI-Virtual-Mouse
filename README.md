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

- `Windows.py` — Windows version of the virtual mouse
- `macOS.py` — macOS version of the virtual mouse
- `requirements.txt` — Pinned Python dependencies required by the project
- `hand_landmarker.task` — MediaPipe hand landmark model

## Requirements

- Python 3.x
- A working webcam
- Camera and accessibility permissions on macOS
- A virtual environment is recommended

## Setup

### Windows (PowerShell)

python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

### macOS

python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

## Run the Project

### Windows

python Windows.py

### macOS

python3 macOS.py


Make sure `hand_landmarker.task` is in the location expected by the selected Python script.

## Notes

- The `venv` folder should not be uploaded to GitHub. Each operating system should have its own Python environment.
- On macOS, allow camera access and the required Accessibility permissions for mouse control.
- Gesture recognition can be affected by lighting, camera quality, and background conditions.
- The project is a prototype and may not work identically across all applications or computers.
- Use the operating-system-specific Python file for the corresponding platform.

## Author

Created as a learning project exploring computer vision and gesture-based human-computer interaction.
