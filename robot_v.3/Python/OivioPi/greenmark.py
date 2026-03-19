import os
from time import monotonic, sleep

import cv2
import numpy as np
import pygame
from gpiozero import Motor

# Motor pins (same as linefollowing.py)
LEFT_MOTOR_FORWARD_PIN = 20
LEFT_MOTOR_BACKWARD_PIN = 9
RIGHT_MOTOR_FORWARD_PIN = 6
RIGHT_MOTOR_BACKWARD_PIN = 5

# Camera tuning
CAMERA_INDEX = int(os.environ.get("CAMERA_INDEX", "0"))
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
ROI_TOP_RATIO = 0.42

# Green marker detection (HSV)
GREEN_MIN = np.array([40, 50, 35], dtype=np.uint8)
GREEN_MAX = np.array([90, 255, 255], dtype=np.uint8)
GREEN_MIN_CONTOUR_AREA = 220
MARKER_TOLERANCE_FROM_CENTER = 20
MARKER_COOLDOWN_SEC = 0.9

# Marker action scripts: (left_speed, right_speed, duration_sec)
ACTION_SCRIPTS = {
    "left": [(-0.45, 0.45, 0.33)],
    "right": [(0.45, -0.45, 0.33)],
    "u_turn": [(0.00, 0.00, 0.07), (0.55, -0.55, 0.60)],
}

left_motor = Motor(
    forward=LEFT_MOTOR_FORWARD_PIN,
    backward=LEFT_MOTOR_BACKWARD_PIN,
    pwm=True,
)
right_motor = Motor(
    forward=RIGHT_MOTOR_FORWARD_PIN,
    backward=RIGHT_MOTOR_BACKWARD_PIN,
    pwm=True,
)


def clamp(value, low, high):
    return max(low, min(high, value))


def set_motor_speeds(left_speed, right_speed):
    left_speed = clamp(left_speed, -1.0, 1.0)
    right_speed = clamp(right_speed, -1.0, 1.0)

    if left_speed >= 0:
        left_motor.forward(left_speed)
    else:
        left_motor.backward(-left_speed)

    if right_speed >= 0:
        right_motor.forward(right_speed)
    else:
        right_motor.backward(-right_speed)


def stop():
    left_motor.stop()
    right_motor.stop()


def _clean_mask(mask):
    kernel = np.ones((3, 3), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    return mask


def detect_green_positions(frame):
    """Return ROI, mask, marker x-positions and valid contours in ROI coordinates."""
    height = frame.shape[0]
    roi_top = int(height * ROI_TOP_RATIO)
    roi = frame[roi_top:, :]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    green_mask = cv2.inRange(hsv, GREEN_MIN, GREEN_MAX)
    green_mask = _clean_mask(green_mask)

    positions_x = []
    valid_contours = []
    contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if cv2.contourArea(cnt) < GREEN_MIN_CONTOUR_AREA:
            continue
        m = cv2.moments(cnt)
        if m["m00"] == 0:
            continue
        gx = int(m["m10"] / m["m00"])
        positions_x.append(gx)
        valid_contours.append(cnt)

    return roi_top, green_mask, positions_x, valid_contours


def decide_action(green_positions, center_x):
    if not green_positions:
        return None, 0, 0

    left_count = 0
    right_count = 0
    for gx in green_positions:
        if gx < (center_x - MARKER_TOLERANCE_FROM_CENTER):
            left_count += 1
        elif gx > (center_x + MARKER_TOLERANCE_FROM_CENTER):
            right_count += 1

    if left_count >= 1 and right_count >= 1:
        return "u_turn", left_count, right_count
    if left_count >= 1:
        return "left", left_count, right_count
    if right_count >= 1:
        return "right", left_count, right_count
    return None, left_count, right_count


def main():
    pygame.init()
    pygame.display.set_mode((220, 120))  # Dummy window for keyboard events
    pygame.display.set_caption("OivioPi Green Marker Only")

    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open webcam index {CAMERA_INDEX}. Try CAMERA_INDEX=1.")

    running = True
    paused = False
    marker_cooldown_until = 0.0

    current_action = None
    action_script = []
    action_idx = 0
    action_step_ends_at = 0.0

    def start_action(action_name, now_ts):
        nonlocal current_action, action_script, action_idx, action_step_ends_at
        action_script = ACTION_SCRIPTS[action_name]
        current_action = action_name
        action_idx = 0
        left_spd, right_spd, duration = action_script[action_idx]
        set_motor_speeds(left_spd, right_spd)
        action_step_ends_at = now_ts + duration

    def tick_action(now_ts):
        nonlocal current_action, action_idx, action_step_ends_at
        if current_action is None:
            return False
        if now_ts < action_step_ends_at:
            return True

        action_idx += 1
        if action_idx >= len(action_script):
            current_action = None
            stop()
            return False

        left_spd, right_spd, duration = action_script[action_idx]
        set_motor_speeds(left_spd, right_spd)
        action_step_ends_at = now_ts + duration
        return True

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key == pygame.K_p:
                        paused = not paused
                        if paused:
                            stop()

            ok, frame = cap.read()
            if not ok:
                stop()
                sleep(0.02)
                continue

            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            now = monotonic()
            roi_top, green_mask, green_positions, green_contours = detect_green_positions(frame)
            frame_mid_x = frame.shape[1] // 2
            status = "IDLE"

            if paused:
                stop()
                current_action = None
                status = "PAUSED"
            else:
                if tick_action(now):
                    status = f"ACTION_{current_action.upper()}"
                else:
                    action, left_mk, right_mk = decide_action(green_positions, frame_mid_x)
                    if action and now >= marker_cooldown_until:
                        start_action(action, now)
                        marker_cooldown_until = now + MARKER_COOLDOWN_SEC
                        status = f"{action.upper()} L{left_mk} R{right_mk}"
                    else:
                        # No line-follow behavior: stay stopped if no marker action.
                        stop()
                        status = "WAIT_GREEN"

            # Debug display
            cv2.rectangle(
                frame, (0, roi_top), (frame.shape[1] - 1, frame.shape[0] - 1), (255, 0, 0), 2
            )
            cv2.line(
                frame, (frame_mid_x, roi_top), (frame_mid_x, frame.shape[0]), (255, 255, 0), 2
            )

            for cnt in green_contours:
                cnt_shifted = cnt.copy()
                cnt_shifted[:, 0, 1] += roi_top
                cv2.drawContours(frame, [cnt_shifted], -1, (0, 255, 0), 2)

            for gx in green_positions:
                cv2.circle(frame, (gx, roi_top + 12), 6, (0, 255, 0), -1)

            cv2.putText(
                frame,
                status,
                (10, 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.62,
                (0, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                f"Green:{len(green_positions)}",
                (10, 46),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                (255, 255, 255),
                1,
            )

            cv2.imshow("OivioPi Green Marker", frame)
            cv2.imshow("Green Mask", green_mask)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                running = False

            sleep(0.01)
    finally:
        stop()
        cap.release()
        cv2.destroyAllWindows()
        pygame.quit()


if __name__ == "__main__":
    main()
