import os
from time import monotonic, sleep

import cv2
import numpy as np
import pygame
from gpiozero import DistanceSensor, Motor

# Motor pins from OivioPi example
LEFT_MOTOR_FORWARD_PIN = 20
LEFT_MOTOR_BACKWARD_PIN = 9
RIGHT_MOTOR_FORWARD_PIN = 6
RIGHT_MOTOR_BACKWARD_PIN = 5

# Ultrasonic pins (HC-SR04 style)
US_TRIG_PIN = int(os.environ.get("US_TRIG_PIN", "26"))
US_ECHO_PIN = int(os.environ.get("US_ECHO_PIN", "27"))
US_OBSTACLE_CM = float(os.environ.get("US_OBSTACLE_CM", "18.0"))
US_MAX_DISTANCE_M = float(os.environ.get("US_MAX_DISTANCE_M", "2.0"))
US_QUEUE_LEN = int(os.environ.get("US_QUEUE_LEN", "3"))
US_COOLDOWN_SEC = float(os.environ.get("US_COOLDOWN_SEC", "1.3"))

# Camera / control tuning
CAMERA_INDEX = int(os.environ.get("CAMERA_INDEX", "0"))
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
ROI_TOP_RATIO = 0.42

# Line follow behavior
BASE_SPEED = 0.42
KP_TURN = 0.95
MAX_TURN = 0.55
SEARCH_SPEED = 0.28
LINE_MIN_CONTOUR_AREA = 280
LOST_LINE_THRESHOLD_FRAMES = 40

# Rejoin behavior after obstacle avoid
REJOIN_STABLE_FRAMES = int(os.environ.get("REJOIN_STABLE_FRAMES", "8"))
REJOIN_TIMEOUT_SEC = float(os.environ.get("REJOIN_TIMEOUT_SEC", "3.0"))

# Black line detection (HSV)
BLACK_MIN = np.array([0, 0, 0], dtype=np.uint8)
BLACK_MAX = np.array([179, 255, 76], dtype=np.uint8)

# Avoid-right scripted steps: (name, left_speed, right_speed, duration_sec)
AVOID_RIGHT_SCRIPT = [
    ("RIGHT_TURN", 0.46, -0.46, 0.34),
    ("BYPASS_FWD", 0.42, 0.42, 0.58),
    ("LEFT_TURN", -0.46, 0.46, 0.31),
]

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
    """Set motor speeds in range -1.0..1.0 (negative = reverse)."""
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


def detect_line(frame):
    """
    Returns:
      line_center: (x, y) in full frame, or None
      black_mask: binary mask line ROI
      roi_top: ROI start y
      line_contour: selected contour in ROI coords, or None
    """
    height = frame.shape[0]
    roi_top = int(height * ROI_TOP_RATIO)
    roi = frame[roi_top:, :]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    black_mask = cv2.inRange(hsv, BLACK_MIN, BLACK_MAX)
    black_mask = _clean_mask(black_mask)

    contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    line_center = None
    line_contour = None

    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) >= LINE_MIN_CONTOUR_AREA:
            m_line = cv2.moments(largest)
            if m_line["m00"] > 0:
                cx = int(m_line["m10"] / m_line["m00"])
                cy = int(m_line["m01"] / m_line["m00"])
                line_center = (cx, cy + roi_top)
                line_contour = largest

    return line_center, black_mask, roi_top, line_contour


def main():
    pygame.init()
    pygame.display.set_mode((220, 120))  # Dummy window for keyboard events
    pygame.display.set_caption("OivioPi Obstacle Avoid + Line Follow")

    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open webcam index {CAMERA_INDEX}. Try CAMERA_INDEX=1.")

    # Ultrasonic setup
    ultrasonic_ok = True
    try:
        us = DistanceSensor(
            echo=US_ECHO_PIN,
            trigger=US_TRIG_PIN,
            max_distance=US_MAX_DISTANCE_M,
            queue_len=US_QUEUE_LEN,
        )
    except Exception:
        us = None
        ultrasonic_ok = False

    running = True
    paused = False

    last_seen_x = None
    lost_line_counter = 0

    mode = "TRACK"  # TRACK, AVOID, REJOIN
    avoid_step_idx = 0
    avoid_step_ends_at = 0.0
    rejoin_start = 0.0
    rejoin_seen_count = 0
    obstacle_cooldown_until = 0.0

    def read_distance_cm():
        if us is None:
            return -1.0
        try:
            return float(us.distance) * 100.0
        except Exception:
            return -1.0

    def start_avoid(now_ts):
        nonlocal mode, avoid_step_idx, avoid_step_ends_at
        mode = "AVOID"
        avoid_step_idx = 0
        _, left_spd, right_spd, duration = AVOID_RIGHT_SCRIPT[avoid_step_idx]
        set_motor_speeds(left_spd, right_spd)
        avoid_step_ends_at = now_ts + duration

    def tick_avoid(now_ts):
        nonlocal mode, avoid_step_idx, avoid_step_ends_at
        if mode != "AVOID":
            return False
        if now_ts < avoid_step_ends_at:
            return True

        avoid_step_idx += 1
        if avoid_step_idx >= len(AVOID_RIGHT_SCRIPT):
            return False

        _, left_spd, right_spd, duration = AVOID_RIGHT_SCRIPT[avoid_step_idx]
        set_motor_speeds(left_spd, right_spd)
        avoid_step_ends_at = now_ts + duration
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
            line_center, line_mask, roi_top, line_contour = detect_line(frame)
            frame_mid_x = frame.shape[1] // 2
            dist_cm = read_distance_cm()
            obstacle = ultrasonic_ok and dist_cm > 0 and dist_cm <= US_OBSTACLE_CM
            status = "IDLE"

            if paused:
                stop()
                status = "PAUSED"
                mode = "TRACK"
                rejoin_seen_count = 0
            else:
                if mode == "AVOID":
                    if tick_avoid(now):
                        step_name = AVOID_RIGHT_SCRIPT[avoid_step_idx][0]
                        status = f"AVOID:{step_name}"
                    else:
                        mode = "REJOIN"
                        rejoin_start = now
                        rejoin_seen_count = 0
                        obstacle_cooldown_until = now + US_COOLDOWN_SEC

                if mode == "REJOIN":
                    if line_center is not None:
                        error = (line_center[0] - frame_mid_x) / float(frame_mid_x)
                        turn = clamp(KP_TURN * error, -MAX_TURN, MAX_TURN)
                        left_speed = BASE_SPEED + turn
                        right_speed = BASE_SPEED - turn
                        set_motor_speeds(left_speed, right_speed)
                        rejoin_seen_count += 1
                        status = f"REJOIN err={error:+.2f} seen={rejoin_seen_count}"
                        if rejoin_seen_count >= REJOIN_STABLE_FRAMES:
                            mode = "TRACK"
                            lost_line_counter = 0
                    else:
                        rejoin_seen_count = 0
                        # Bias left to merge back to original line after bypassing right.
                        set_motor_speeds(-SEARCH_SPEED, SEARCH_SPEED)
                        status = "REJOIN_SEARCH_LEFT"

                    if (now - rejoin_start) > REJOIN_TIMEOUT_SEC:
                        mode = "TRACK"

                if mode == "TRACK":
                    if obstacle and now >= obstacle_cooldown_until:
                        start_avoid(now)
                        status = f"OBSTACLE {dist_cm:.1f}cm -> RIGHT"
                    elif line_center is not None:
                        error = (line_center[0] - frame_mid_x) / float(frame_mid_x)
                        turn = clamp(KP_TURN * error, -MAX_TURN, MAX_TURN)
                        left_speed = BASE_SPEED + turn
                        right_speed = BASE_SPEED - turn
                        set_motor_speeds(left_speed, right_speed)
                        last_seen_x = line_center[0]
                        lost_line_counter = 0
                        status = f"TRACK err={error:+.2f}"
                    else:
                        lost_line_counter += 1
                        if last_seen_x is not None and lost_line_counter < LOST_LINE_THRESHOLD_FRAMES:
                            if last_seen_x < frame_mid_x:
                                set_motor_speeds(-SEARCH_SPEED, SEARCH_SPEED)
                                status = f"LOST->LEFT ({lost_line_counter})"
                            else:
                                set_motor_speeds(SEARCH_SPEED, -SEARCH_SPEED)
                                status = f"LOST->RIGHT ({lost_line_counter})"
                        else:
                            set_motor_speeds(-SEARCH_SPEED, SEARCH_SPEED)
                            status = f"SEARCH ({lost_line_counter})"

            # --- Debug overlays ---
            cv2.rectangle(
                frame,
                (0, roi_top),
                (frame.shape[1] - 1, frame.shape[0] - 1),
                (255, 0, 0),
                2,
            )
            cv2.line(
                frame,
                (frame_mid_x, roi_top),
                (frame_mid_x, frame.shape[0]),
                (255, 255, 0),
                2,
            )

            if line_contour is not None:
                cnt_shifted = line_contour.copy()
                cnt_shifted[:, 0, 1] += roi_top
                cv2.drawContours(frame, [cnt_shifted], -1, (0, 165, 255), 2)

            if line_center is not None:
                cv2.circle(frame, line_center, 6, (0, 255, 255), -1)

            dist_text = f"US:{dist_cm:.1f}cm" if dist_cm >= 0 else "US:N/A"
            cv2.putText(
                frame,
                status,
                (10, 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.58,
                (0, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                f"{dist_text} mode={mode}",
                (10, 46),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (255, 255, 255),
                1,
            )

            cv2.imshow("OivioPi Obstacle Avoid", frame)
            cv2.imshow("Line Mask", line_mask)

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

