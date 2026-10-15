import cv2
import mediapipe as mp
import pyautogui
import math
import time


# ============================================================
# MEDIAPIPE SETUP
# ============================================================

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path="hand_landmarker.task"
    ),
    running_mode=RunningMode.IMAGE,
    num_hands=1,
    min_hand_detection_confidence=0.4
)

landmarker = HandLandmarker.create_from_options(options)


# ============================================================
# WEBCAM SETUP
# ============================================================

cap = cv2.VideoCapture(0)


# ============================================================
# SCREEN SIZE
# ============================================================

screen_width, screen_height = pyautogui.size()


# ============================================================
# CURSOR SETTINGS
# ============================================================

smoothing = 0.35

prev_x = None
prev_y = None

active_min = 0.05
active_max = 0.95


# ============================================================
# CURSOR LOCK
# ============================================================

cursor_locked = False


# ============================================================
# CLICK STATES
# ============================================================

left_click_active = False
right_click_active = False


# Single and double-click detection

pending_left_click = False
last_left_click_time = 0
double_click_interval = 0.5


# ============================================================
# DRAG AND DROP STATE
# ============================================================

drag_active = False


# ============================================================
# SCROLL SETTINGS
# ============================================================

scroll_delay = 0.06
last_scroll_time = 0


# ============================================================
# ZOOM SETTINGS
# ============================================================

last_zoom_time = 0
zoom_cooldown = 0.8


# ============================================================
# START
# ============================================================

print("AI Virtual Mouse Started on Windows")
print()
print("Only Index Up       = Move Cursor")
print("All Fingers Up      = Lock Cursor")
print("All Fingers Up + Thumb-Index Pinch = Single Left Click")
print("All Fingers Up + Thumb-Index Pinch (2 times) = Double Left Click")
print("Index + Pinky Up    = Right Click")
print("Index-Middle Fingers Up = Scroll Up")
print("Index-Middle-Ring Fingers Up = Scroll Down")
print("Pinky Only Up = Zoom Out (Ctrl + -)")
print("Ring + Pinky Up = Zoom In (Ctrl + Shift + =)")
print("Cursor Locked + Thumb Only Up = Drag")
print("All Four Fingers Up = Drop")
print()
print("First open Camera then Press 'q' to quit.")


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    # --------------------------------------------------------
    # READ CAMERA FRAME
    # --------------------------------------------------------

    ret, frame = cap.read()

    if not ret:
        break


    # --------------------------------------------------------
    # MIRROR WEBCAM
    # --------------------------------------------------------

    frame = cv2.flip(frame, 1)


    # --------------------------------------------------------
    # CONVERT BGR → RGB
    # --------------------------------------------------------

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


    # --------------------------------------------------------
    # CONVERT FRAME TO MEDIAPIPE IMAGE
    # --------------------------------------------------------

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )


    # --------------------------------------------------------
    # DETECT HAND
    # --------------------------------------------------------

    result = landmarker.detect(mp_image)


    # ========================================================
    # HAND DETECTED
    # ========================================================

    if result.hand_landmarks:

        hand = result.hand_landmarks[0]


        # ----------------------------------------------------
        # LANDMARKS
        # ----------------------------------------------------

        thumb_tip = hand[4]
        index_tip = hand[8]
        middle_tip = hand[12]
        ring_tip = hand[16]
        pinky_tip = hand[20]


        # ----------------------------------------------------
        # FINGER STATES
        # ----------------------------------------------------

        index_up = index_tip.y < hand[6].y
        middle_up = middle_tip.y < hand[10].y
        ring_up = ring_tip.y < hand[14].y
        pinky_up = pinky_tip.y < hand[18].y


        # ====================================================
        # THUMB-UP DRAG GESTURE
        # ====================================================

        thumb_up = thumb_tip.y < hand[3].y

        thumb_only = (
            thumb_up
            and not index_up
            and not middle_up
            and not ring_up
            and not pinky_up
        )


        # ====================================================
        # INDEX ONLY
        # ====================================================

        index_only = (
            index_up
            and not middle_up
            and not ring_up
            and not pinky_up
        )


        # ====================================================
        # ALL FOUR FINGERS UP
        # ====================================================

        all_fingers_up = (
            index_up
            and middle_up
            and ring_up
            and pinky_up
        )


        # ====================================================
        # LEFT CLICK
        # ====================================================

        left_distance = math.hypot(
            thumb_tip.x - index_tip.x,
            thumb_tip.y - index_tip.y
        )

        left_click = (
            all_fingers_up
            and left_distance < 0.10
        )


        # ====================================================
        # RIGHT CLICK
        # ====================================================

        right_click = (
            index_up
            and not middle_up
            and not ring_up
            and pinky_up
        )


        # ====================================================
        # FINGER ATTACHMENT FOR SCROLLING
        # ====================================================

        finger_distance = math.hypot(
            index_tip.x - middle_tip.x,
            index_tip.y - middle_tip.y
        )

        fingers_attached = finger_distance < 0.12


        # ====================================================
        # SCROLL GESTURES
        # ====================================================

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


        # ====================================================
        # ZOOM GESTURE DETECTION
        # ====================================================

        # Pinky only → Zoom Out

        zoom_out_gesture = (
            pinky_up
            and not ring_up
            and not index_up
            and not middle_up
        )


        # Ring + Pinky → Zoom In

        zoom_in_gesture = (
            ring_up
            and pinky_up
            and not index_up
            and not middle_up
        )


        # ====================================================
        # SINGLE AND DOUBLE LEFT CLICK
        # ====================================================

        current_time = time.time()

        if cursor_locked and left_click:

            if not left_click_active:

                if (
                    pending_left_click
                    and current_time - last_left_click_time
                    <= double_click_interval
                ):

                    # Second pinch detected → Double click

                    pyautogui.doubleClick()

                    pending_left_click = False

                    cv2.putText(
                        frame,
                        "DOUBLE CLICK",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2
                    )

                else:

                    # First pinch → Wait for possible second pinch

                    pending_left_click = True
                    last_left_click_time = current_time

                left_click_active = True

        else:

            left_click_active = False


        # ----------------------------------------------------
        # PERFORM SINGLE CLICK
        # ----------------------------------------------------

        if (
            pending_left_click
            and current_time - last_left_click_time
            > double_click_interval
        ):

            pyautogui.click()

            pending_left_click = False

            cv2.putText(
                frame,
                "LEFT CLICK",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )


        # ====================================================
        # RIGHT CLICK ACTION
        # ====================================================

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


        # ====================================================
        # SCROLL ACTION
        # ====================================================

        if (
            not left_click
            and not right_click
            and not zoom_in_gesture
            and not zoom_out_gesture
        ):

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


        # ====================================================
        # ZOOM IN / ZOOM OUT
        # ====================================================

        current_time = time.time()

        if not drag_active and (
            zoom_in_gesture
            or zoom_out_gesture
        ):

            # Prevent repeated zoom actions

            if current_time - last_zoom_time >= zoom_cooldown:

                # Zoom In

                if zoom_in_gesture:

                    pyautogui.hotkey(
                        "ctrl",
                        "shift",
                        "="
                    )

                    cv2.putText(
                        frame,
                        "ZOOM IN",
                        (20, 240),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2
                    )


                # Zoom Out

                elif zoom_out_gesture:

                    pyautogui.hotkey(
                        "ctrl",
                        "-"
                    )

                    cv2.putText(
                        frame,
                        "ZOOM OUT",
                        (20, 240),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 165, 255),
                        2
                    )

                last_zoom_time = current_time


        # ====================================================
        # THUMB-UP DRAG AND DROP
        # ====================================================

        if cursor_locked:

            # Start dragging with only thumb up

            if thumb_only:

                if not drag_active:

                    pyautogui.mouseDown()
                    drag_active = True


                # Track thumb tip

                mapped_x = max(
                    active_min,
                    min(thumb_tip.x, active_max)
                )

                mapped_y = max(
                    active_min,
                    min(thumb_tip.y, active_max)
                )


                current_x = (
                    (mapped_x - active_min)
                    / (active_max - active_min)
                ) * screen_width


                current_y = (
                    (mapped_y - active_min)
                    / (active_max - active_min)
                ) * screen_height


                # Move cursor while holding mouse button

                pyautogui.moveTo(
                    int(current_x),
                    int(current_y)
                )


                cv2.putText(
                    frame,
                    "DRAGGING",
                    (20, 200),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 255),
                    2
                )


            # Release mouse button to drop

            elif drag_active and all_fingers_up:

                pyautogui.mouseUp()
                drag_active = False

                cv2.putText(
                    frame,
                    "DROP",
                    (20, 200),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )


        # ====================================================
        # CURSOR CONTROL
        # ====================================================

        if not cursor_locked:

            # ------------------------------------------------
            # MOVE CURSOR
            # ------------------------------------------------

            if index_only:

                # Convert webcam coordinates to screen coordinates

                mapped_x = max(
                    active_min,
                    min(index_tip.x, active_max)
                )

                mapped_y = max(
                    0.02,
                    min(index_tip.y, 0.98)
                )


                current_x = (
                    (mapped_x - active_min)
                    / (active_max - active_min)
                ) * screen_width


                current_y = (
                    (mapped_y - 0.02)
                    / (0.98 - 0.02)
                ) * screen_height


                # Initialize cursor position on first movement

                if prev_x is None or prev_y is None:

                    smooth_x = current_x
                    smooth_y = current_y

                else:

                    # Apply exponential smoothing

                    smooth_x = (
                        prev_x
                        + (current_x - prev_x)
                        * smoothing
                    )

                    smooth_y = (
                        prev_y
                        + (current_y - prev_y)
                        * smoothing
                    )


                # Move real mouse cursor

                pyautogui.moveTo(
                    int(smooth_x),
                    int(smooth_y),
                    _pause=False
                )


                # Save current cursor position

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


            # ------------------------------------------------
            # LOCK CURSOR
            # ------------------------------------------------

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


        # ====================================================
        # WHEN CURSOR IS LOCKED
        # ====================================================

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


    # ========================================================
    # NO HAND DETECTED
    # ========================================================

    else:

        # Release active drag if hand is no longer detected

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


    # ========================================================
    # SHOW WEBCAM
    # ========================================================

    cv2.imshow(
        "AI Virtual Mouse",
        frame
    )


    # ========================================================
    # PRESS Q TO QUIT
    # ========================================================

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# ============================================================
# CLEANUP
# ============================================================

if drag_active:

    pyautogui.mouseUp()

cap.release()
landmarker.close()
cv2.destroyAllWindows()