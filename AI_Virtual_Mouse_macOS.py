import cv2

import mediapipe as mp

import pyautogui

import math

import time

# On macOS, grant this terminal/Python app Camera and Accessibility permissions.
# Move the mouse to the top-left corner to trigger PyAutoGUI's emergency fail-safe.
pyautogui.FAILSAFE = True

# MEDIAPIPE SETUP

BaseOptions = mp.tasks.BaseOptions

HandLandmarker = mp.tasks.vision.HandLandmarker

HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions

RunningMode = mp.tasks.vision.RunningMode

# options = HandLandmarkerOptions(

#     base_options=BaseOptions(

#         model_asset_path="hand_landmarker.task"

#     ),

#     running_mode=RunningMode.IMAGE

# )

options = HandLandmarkerOptions(

    base_options=BaseOptions(

        model_asset_path="hand_landmarker.task"

    ),

    running_mode=RunningMode.IMAGE,

    num_hands=1,

    min_hand_detection_confidence=0.4

)

landmarker = HandLandmarker.create_from_options(options)

# WEBCAM SETUP (macOS first, with fallback)
# macOS OpenCV usually uses AVFoundation for built-in cameras.
cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
if not cap.isOpened():
    cap.release()
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError(
        "Camera could not be opened. Check macOS Camera permission and close apps using the camera."
    )

# Request a modest resolution; the camera may choose a supported size.
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# SCREEN SIZE

screen_width, screen_height = pyautogui.size()

# SMOOTHING

# smoothing = 0.2

smoothing = 0.15

# prev_x = 0

# prev_y = 0

prev_x = None

prev_y = None

# ACTIVE REGION

active_min = 0.1

active_max = 0.9

# CURSOR LOCK

cursor_locked = False

# CLICK STATES

left_click_active = False

right_click_active = False

# Single and double-click detection

pending_left_click = False

last_left_click_time = 0

double_click_interval = 0.5

# double_click_interval = 1.0

# DRAG AND DROP STATE

drag_active = False

# SCROLL SETTINGS

scroll_delay = 0.06

last_scroll_time = 0

# START

print("AI Virtual Mouse Started on macOS / Windows")

print()

print("Only Index Up       = Move Cursor")

print("All Fingers Up      = Lock Cursor")

print("All Fingers Up + Thumb-Index Pinch = Left Click")

print("Index + Pinky Up    = Right Click")

print("Index-Middle Fingers Up       = Scroll Up")

print("Index-Middle-Ring Fingers Up = Scroll Down")
print("Cursor Locked + Thumb Only Up = Drag")
print("All Four Fingers Up = Drop")

print()

print("Press 'q' to quit.")

# MAIN LOOP

while True:

    ret, frame = cap.read()

    if not ret:

        break

    # Mirror webcam

    frame = cv2.flip(frame, 1)

    # Convert BGR → RGB

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert frame to MediaPipe image

    mp_image = mp.Image(

        image_format=mp.ImageFormat.SRGB,

        data=rgb_frame

    )

    # Detect hand

    result = landmarker.detect(mp_image)

    # HAND DETECTED

    if result.hand_landmarks:

        hand = result.hand_landmarks[0]

        print("HAND DETECTED")

        # LANDMARKS

        thumb_tip = hand[4]

        index_tip = hand[8]

        middle_tip = hand[12]

        ring_tip = hand[16]

        pinky_tip = hand[20]

        # FINGER STATES

        index_up = index_tip.y < hand[6].y

        middle_up = middle_tip.y < hand[10].y

        ring_up = ring_tip.y < hand[14].y

        pinky_up = pinky_tip.y < hand[18].y

        # THUMB-UP DRAG GESTURE

        # Thumb tip (landmark 4) must be above thumb joint (landmark 3)

        thumb_up = thumb_tip.y < hand[3].y

        # Only thumb up; all four other fingers must be down

        thumb_only = (

            thumb_up

            and not index_up

            and not middle_up

            and not ring_up

            and not pinky_up

        )

        # INDEX ONLY

        index_only = (

            index_up

            and not middle_up

            and not ring_up

            and not pinky_up

        )

        # ALL FOUR FINGERS UP

        all_fingers_up = (

            index_up

            and middle_up

            and ring_up

            and pinky_up

        )

        # LEFT CLICK

        # Distance between thumb and index finger

        left_distance = math.hypot(

            thumb_tip.x - index_tip.x,

            thumb_tip.y - index_tip.y

        )

        # All fingers up + thumb-index pinch

        left_click = (

            all_fingers_up

            and left_distance < 0.10

        )

        # RIGHT CLICK

        # Index + Pinky UP

        # Middle + Ring DOWN

        right_click = (

            index_up

            and not middle_up

            and not ring_up

            and pinky_up

        )

        # FINGER ATTACHMENT FOR SCROLLING

        finger_distance = math.hypot(

            index_tip.x - middle_tip.x,

            index_tip.y - middle_tip.y

        )

        fingers_attached = finger_distance < 0.12

        # SCROLL GESTURES

        # 2 fingers up → Scroll Up

        scroll_up = (

            index_up

            and middle_up

            and not ring_up

            and not pinky_up

            and fingers_attached

        )

        # 3 fingers up → Scroll Down

        scroll_down = (

            index_up

            and middle_up

            and ring_up

            and not pinky_up

            and fingers_attached

        )

        # SINGLE AND DOUBLE LEFT CLICK

        current_time = time.time()

        if cursor_locked and left_click:

            if not left_click_active:

                if (

                    pending_left_click

                    and current_time - last_left_click_time

                    <= double_click_interval

                ):

                    # Second pinch detected: double-click

                    pyautogui.doubleClick()

                    pending_left_click = False

                    cv2.putText(

                        frame, "DOUBLE CLICK", (20, 40),

                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2

                    )

                else:

                    # First pinch: wait for a possible second pinch

                    pending_left_click = True

                    last_left_click_time = current_time

                left_click_active = True

        else:

            left_click_active = False

        # Perform single-click if no second pinch arrives in time

        if (

            pending_left_click

            and current_time - last_left_click_time > double_click_interval

        ):

            pyautogui.click()

            pending_left_click = False

            cv2.putText(

                frame, "LEFT CLICK", (20, 40),

                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2

            )

        # RIGHT CLICK ACTION

        if cursor_locked and right_click:

            if not right_click_active:

                pyautogui.rightClick()

                right_click_active = True

            cv2.putText(

                frame,

                "RIGHT CLICK",

                (20, 80),

                cv2.FONT_HERSHEY_SIMPLEX,

                1,

                (0, 0, 255),

                2

            )

        else:

            right_click_active = False

        # SCROLL ACTION

        if not left_click and not right_click:

            current_time = time.time()

            if current_time - last_scroll_time >= scroll_delay:

                # Scroll Up

                if scroll_up:

                    pyautogui.scroll(100)

                    last_scroll_time = current_time

                # Scroll Down

                elif scroll_down:

                    pyautogui.scroll(-100)

                    last_scroll_time = current_time

        # THUMB-UP DRAG AND DROP

        if cursor_locked:

            # Start dragging with only thumb up

            if thumb_only:

                if not drag_active:

                    pyautogui.mouseDown()

                    drag_active = True

                # Track thumb tip: landmark 4

                mapped_x = max(active_min, min(thumb_tip.x, active_max))

                mapped_y = max(active_min, min(thumb_tip.y, active_max))

                current_x = (

                    (mapped_x - active_min) / (active_max - active_min)

                ) * screen_width

                current_y = (

                    (mapped_y - active_min) / (active_max - active_min)

                ) * screen_height

                # Move cursor while holding the mouse button

                pyautogui.moveTo(int(current_x), int(current_y))

                cv2.putText(

                    frame, "DRAGGING", (20, 200),

                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2

                )

            # Release the mouse button to drop

            elif drag_active and all_fingers_up:

                pyautogui.mouseUp()

                drag_active = False

                cv2.putText(

                    frame, "DROP", (20, 200),

                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2

                )

        # CURSOR CONTROL

        if not cursor_locked:

            # MOVE CURSOR

            if index_only:

                # Apply active region

                # mapped_x = max(active_min,min(index_tip.x, active_max))

                # mapped_y = max(active_min,min(index_tip.y, active_max))

                # Use a wider vertical range for cursor movement

                mapped_x = max(0.05, min(index_tip.x, 0.95))

                mapped_y = max(0.02, min(index_tip.y, 0.98))

                # Convert webcam coordinates to screen

                current_x = (

                    (mapped_x - 0.05) / (0.95 - 0.05)

                ) * screen_width

                current_y = (

                    (mapped_y - 0.02) / (0.98 - 0.02)

                ) * screen_height

                # Apply smoothing

                # smooth_x = (prev_x + (current_x - prev_x) * smoothing)

                # smooth_y = (prev_y + (current_y - prev_y) * smoothing)

                # Initialize cursor position on the first movement

                if prev_x is None or prev_y is None:

                    smooth_x = current_x

                    smooth_y = current_y

                else:

                # Apply exponential smoothing

                    smooth_x = prev_x + (current_x - prev_x) * smoothing

                    smooth_y = prev_y + (current_y - prev_y) * smoothing

                # Move real mouse cursor

                pyautogui.moveTo(

                    int(smooth_x),

                    int(smooth_y)

                )

                # Save current position

                prev_x = smooth_x

                prev_y = smooth_y

                cv2.putText(

                    frame,

                    "MOVING",

                    (20, 120),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    1,

                    (255, 255, 0),

                    2

                )

            # LOCK CURSOR

            elif all_fingers_up and not left_click:

                cursor_locked = True

                cv2.putText(

                    frame,

                    "CURSOR LOCKED",

                    (20, 120),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    1,

                    (255, 255, 0),

                    2

                )

        # WHEN CURSOR IS LOCKED

        else:

            # Unlock with only index finger

            # Do not unlock during thumb-index pinch

            if index_only and left_distance >= 0.10:

                cursor_locked = False

                cv2.putText(

                    frame,

                    "UNLOCKED",

                    (20, 120),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    1,

                    (255, 255, 0),

                    2

                )

            else:

                cv2.putText(

                    frame,

                    "CURSOR LOCKED",

                    (20, 120),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    1,

                    (255, 255, 0),

                    2

                )

    # NO HAND DETECTED

    else:

        # Release an active drag if the hand is no longer detected

        if drag_active:

            pyautogui.mouseUp()

            drag_active = False

        cv2.putText(

            frame,

            "NO HAND",

            (20, 40),

            cv2.FONT_HERSHEY_SIMPLEX,

            1,

            (0, 0, 255),

            2

        )

        print("NO HAND DETECTED")

    # SHOW WEBCAM

    cv2.imshow(

        "AI Virtual Mouse",

        frame

    )

    # Press Q to quit

    if cv2.waitKey(1) & 0xFF == ord('q'):

        break

# CLEANUP

if drag_active:
    pyautogui.mouseUp()

cap.release()
landmarker.close()
cv2.destroyAllWindows()
