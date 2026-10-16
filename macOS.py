import cv2
import mediapipe as mp
import pyautogui
import math
import time

# On macOS, grant this terminal/Python app Camera and Accessibility permissions.
# Move the mouse to the top-left corner to trigger PyAutoGUI's emergency fail-safe.
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.001

# MEDIAPIPE SETUP
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

# WEBCAM SETUP (macOS first, with fallback)
cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
if not cap.isOpened():
    cap.release()
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError(
        "Camera could not be opened. Check macOS Camera permission and close apps using the camera."
    )

# SCREEN SIZE
screen_width, screen_height = pyautogui.size()

# SMOOTHING & COORDINATE BOUNDS
smoothing = 0.15
prev_x = None
prev_y = None

# Active tracking bounds (normalized coords in webcam space)
active_min_x = 0.05
active_max_x = 0.95
active_min_y = 0.05
active_max_y = 0.95


def map_to_screen(norm_x, norm_y):
    """Maps normalized webcam coordinates to screen space without triggering failsafe."""
    clamped_x = max(active_min_x, min(norm_x, active_max_x))
    clamped_y = max(active_min_y, min(norm_y, active_max_y))
    sx = ((clamped_x - active_min_x) / (active_max_x - active_min_x)) * screen_width
    sy = ((clamped_y - active_min_y) / (active_max_y - active_min_y)) * screen_height
    # Avoid (0, 0) failsafe crash while keeping edge reachability
    sx = max(10, min(sx, screen_width - 10))
    sy = max(10, min(sy, screen_height - 10))
    return sx, sy


# CURSOR LOCK
cursor_locked = False

# CLICK STATES
left_click_active = False
right_click_active = False
right_click_consumed = False

# Single and double-click detection
pending_left_click = False
last_left_click_time = 0
double_click_interval = 0.35

# Right-click cooldown (protects context menu from accidental clicks during gesture release)
last_right_click_time = 0
right_click_cooldown = 0.8

# DRAG AND DROP STATE
drag_active = False
drag_offset_x = 0
drag_offset_y = 0
last_drag_time = 0
drag_cooldown = 0.5  # Brief pause after drag/selection to prevent accidental zoom

# SCROLL SETTINGS (adjusted for macOS sensitivity)
scroll_delay = 0.12
last_scroll_time = 0
SCROLL_AMOUNT = 1

# ZOOM SETTINGS (with buffer to prevent accidental triggers during transitions)
last_zoom_time = 0
zoom_cooldown = 0.7
zoom_buffer_count = 0
ZOOM_BUFFER_THRESHOLD = 3

# START
print("=" * 50)
print("AI Virtual Mouse Started on macOS")
print("=" * 50)
print("Only Index Up                  = Move Cursor")
print("All Fingers Up                 = Lock Cursor")
print("All Fingers Up, Index + Thumb Pinch   = Left Click (Single Pinch) / Double Click (Double Pinch)")
print("Index + Pinky Up               = Right Click")
print("Index + Middle Up     = Scroll Up")
print("Index + Middle + Ring Up = Scroll Down")
print("Pinky Only Up                  = Zoom Out (Command + -)")
print("Ring + Pinky Up                = Zoom In (Command + =)")
print("Cursor Locked + Thumb Only Up  = Drag (Smooth & Aligned)")
print("All Four Fingers Up            = Drop")
print("=" * 50)
print("First open Camera then Touch/click on Camera Then Press 'q' to quit.")

# MAIN LOOP
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Mirror webcam
    frame = cv2.flip(frame, 1)

    # Convert BGR -> RGB
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

        # LANDMARKS
        thumb_tip = hand[4]
        index_tip = hand[8]
        middle_tip = hand[12]
        ring_tip = hand[16]
        pinky_tip = hand[20]

        # FINGER EXTENSION STATES
        # In normalized coords, y decreases as finger extends upward
        index_up = index_tip.y < hand[6].y
        middle_up = middle_tip.y < hand[10].y
        ring_up = ring_tip.y < hand[14].y
        pinky_up = pinky_tip.y < hand[18].y
        thumb_up = thumb_tip.y < hand[2].y

        # GESTURES
        thumb_only = (
            thumb_up
            and not index_up
            and not middle_up
            and not ring_up
            and not pinky_up
        )

        index_only = (
            index_up
            and not middle_up
            and not ring_up
            and not pinky_up
        )

        all_fingers_up = (
            index_up
            and middle_up
            and ring_up
            and pinky_up
        )

        # Distance between thumb and index finger
        left_distance = math.hypot(
            thumb_tip.x - index_tip.x,
            thumb_tip.y - index_tip.y
        )

        # Left click pinch: middle, ring, pinky up while thumb & index pinch together
        left_click = (
            middle_up
            and ring_up
            and pinky_up
            and left_distance < 0.065
        )

        # Right click: index and pinky up, others down
        right_click = (
            index_up
            and not middle_up
            and not ring_up
            and pinky_up
        )

        # Fingers attachment for scrolling
        finger_distance = math.hypot(
            index_tip.x - middle_tip.x,
            index_tip.y - middle_tip.y
        )
        ring_distance = math.hypot(
            middle_tip.x - ring_tip.x,
            middle_tip.y - ring_tip.y
        )
        two_fingers_attached = finger_distance < 0.12
        three_fingers_attached = two_fingers_attached and (ring_distance < 0.12)

        scroll_up = (
            index_up
            and middle_up
            and not ring_up
            and not pinky_up
            and two_fingers_attached
        )

        scroll_down = (
            index_up
            and middle_up
            and ring_up
            and not pinky_up
            and three_fingers_attached
        )

        zoom_out_gesture = (
            pinky_up
            and not ring_up
            and not index_up
            and not middle_up
        )

        zoom_in_gesture = (
            ring_up
            and pinky_up
            and not index_up
            and not middle_up
        )

        current_time = time.time()
        drop_just_happened = False

        # --- THUMB-UP DRAG AND DROP ---
        if drag_active:
            # Drop when all fingers are extended, or safety release if switching to index_only
            if all_fingers_up:
                pyautogui.mouseUp()
                drag_active = False
                drop_just_happened = True
                last_drag_time = current_time
                cv2.putText(
                    frame, "DROP", (20, 200),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
                )
            elif index_only:
                # Emergency release on explicit cursor movement gesture
                pyautogui.mouseUp()
                drag_active = False
                last_drag_time = current_time
            elif thumb_only:
                # Smooth continuous drag using macOS native drag events for icons and text
                thumb_sx, thumb_sy = map_to_screen(thumb_tip.x, thumb_tip.y)
                target_x = thumb_sx + drag_offset_x
                target_y = thumb_sy + drag_offset_y
                target_x = max(10, min(target_x, screen_width - 10))
                target_y = max(10, min(target_y, screen_height - 10))

                if prev_x is None or prev_y is None:
                    smooth_x, smooth_y = target_x, target_y
                else:
                    # Responsive smoothing (0.35) quickly passes macOS 5px drag threshold for icons
                    smooth_x = prev_x + (target_x - prev_x) * 0.35
                    smooth_y = prev_y + (target_y - prev_y) * 0.35

                # On macOS, dragTo with button='left' and mouseDownUp=False sends kCGEventLeftMouseDragged
                pyautogui.dragTo(int(smooth_x), int(smooth_y), button='left', mouseDownUp=False)
                prev_x, prev_y = smooth_x, smooth_y

                cv2.putText(
                    frame, "DRAGGING", (20, 200),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2
                )
        else:
            # Start dragging when cursor is locked and user shows thumb_only
            if cursor_locked and thumb_only:
                pyautogui.mouseDown()
                drag_active = True
                thumb_sx, thumb_sy = map_to_screen(thumb_tip.x, thumb_tip.y)
                # Offset eliminates the cursor teleportation jump
                current_cursor_x = prev_x if prev_x is not None else thumb_sx
                current_cursor_y = prev_y if prev_y is not None else thumb_sy
                drag_offset_x = current_cursor_x - thumb_sx
                drag_offset_y = current_cursor_y - thumb_sy

                cv2.putText(
                    frame, "DRAGGING", (20, 200),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2
                )

        # --- RIGHT CLICK ---
        if right_click:
            pending_left_click = False
            left_click_active = False
            last_right_click_time = current_time

            if not right_click_active:
                pyautogui.rightClick()
                right_click_active = True
                right_click_consumed = True

            cv2.putText(
                frame, "RIGHT CLICK", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2
            )
        else:
            right_click_active = False

            # Check if we are still within right-click or drag cooldown
            right_click_in_cooldown = (current_time - last_right_click_time) < right_click_cooldown
            drag_in_cooldown = (current_time - last_drag_time) < drag_cooldown

            if right_click_in_cooldown or drag_in_cooldown:
                # Strictly prevent any left click from triggering right after right-click or drag
                pending_left_click = False
                left_click_active = False

            # --- LEFT CLICK / DOUBLE CLICK ---
            if (
                not right_click_in_cooldown
                and not drag_in_cooldown
                and not drop_just_happened
                and cursor_locked
                and left_click
                and not right_click_consumed
            ):
                if not left_click_active:
                    if (
                        pending_left_click
                        and current_time - last_left_click_time <= double_click_interval
                    ):
                        pyautogui.doubleClick(interval=0.1)
                        pending_left_click = False
                        cv2.putText(
                            frame, "DOUBLE CLICK", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
                        )
                    else:
                        pending_left_click = True
                        last_left_click_time = current_time

                    left_click_active = True
            else:
                if not left_click:
                    left_click_active = False

            # Perform single-click if no second pinch arrives in time
            if (
                not right_click_in_cooldown
                and not drag_in_cooldown
                and pending_left_click
                and not right_click
                and not right_click_consumed
                and current_time - last_left_click_time > double_click_interval
            ):
                pyautogui.click()
                pending_left_click = False
                cv2.putText(
                    frame, "LEFT CLICK", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
                )

        if not right_click and not left_click and (current_time - last_right_click_time >= right_click_cooldown):
            right_click_consumed = False

        # --- SCROLL ACTION ---
        if (
            not drag_active
            and not left_click
            and not right_click
            and not zoom_in_gesture
            and not zoom_out_gesture
        ):
            if current_time - last_scroll_time >= scroll_delay:
                if scroll_up:
                    pyautogui.scroll(SCROLL_AMOUNT)
                    last_scroll_time = current_time
                    cv2.putText(
                        frame, "SCROLL UP", (20, 160),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2
                    )
                elif scroll_down:
                    pyautogui.scroll(-SCROLL_AMOUNT)
                    last_scroll_time = current_time
                    cv2.putText(
                        frame, "SCROLL DOWN", (20, 160),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2
                    )

        # --- ZOOM ACTION (with stability buffer to prevent transition misfires) ---
        drag_in_cooldown = (current_time - last_drag_time) < drag_cooldown
        if not drag_active and not drag_in_cooldown and (zoom_in_gesture or zoom_out_gesture):
            zoom_buffer_count += 1
            if zoom_buffer_count >= ZOOM_BUFFER_THRESHOLD:
                if current_time - last_zoom_time >= zoom_cooldown:
                    if zoom_in_gesture:
                        pyautogui.hotkey("command", "=")
                        zoom_label = "ZOOM IN"
                        zoom_color = (0, 255, 0)
                    else:
                        pyautogui.hotkey("command", "-")
                        zoom_label = "ZOOM OUT"
                        zoom_color = (0, 165, 255)

                    last_zoom_time = current_time
                    cv2.putText(
                        frame, zoom_label, (20, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, zoom_color, 2
                    )
        else:
            zoom_buffer_count = 0

        # --- CURSOR CONTROL & LOCK / UNLOCK ---
        if not drag_active:
            if not cursor_locked:
                # Move Cursor
                if index_only:
                    target_x, target_y = map_to_screen(index_tip.x, index_tip.y)

                    if prev_x is None or prev_y is None:
                        smooth_x, smooth_y = target_x, target_y
                    else:
                        smooth_x = prev_x + (target_x - prev_x) * smoothing
                        smooth_y = prev_y + (target_y - prev_y) * smoothing

                    pyautogui.moveTo(int(smooth_x), int(smooth_y))
                    prev_x = smooth_x
                    prev_y = smooth_y

                    cv2.putText(
                        frame, "MOVING", (20, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2
                    )

                # Lock Cursor with all fingers extended and no pinch
                elif all_fingers_up and not left_click and not drop_just_happened:
                    cursor_locked = True
                    cv2.putText(
                        frame, "CURSOR LOCKED", (20, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2
                    )

            else:
                # Unlock cursor when index_only is shown (and thumb is separated)
                if index_only and left_distance >= 0.10:
                    cursor_locked = False
                    cv2.putText(
                        frame, "UNLOCKED", (20, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2
                    )
                else:
                    cv2.putText(
                        frame, "CURSOR LOCKED", (20, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2
                    )

    # NO HAND DETECTED
    else:
        if drag_active:
            pyautogui.mouseUp()
            drag_active = False
            last_drag_time = time.time()

        pending_left_click = False
        left_click_active = False
        right_click_active = False
        zoom_buffer_count = 0

        cv2.putText(
            frame, "NO HAND", (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2
        )

    # SHOW WEBCAM
    cv2.imshow("AI Virtual Mouse", frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# CLEANUP
if drag_active:
    pyautogui.mouseUp()

cap.release()
landmarker.close()
cv2.destroyAllWindows()