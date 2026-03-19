import os
from time import monotonic, sleep

import cv2
import numpy as np
import pygame
from gpiozero import Motor

# Motor pins from OivioPi example
LEFT_MOTOR_FORWARD_PIN = 20
LEFT_MOTOR_BACKWARD_PIN = 9
RIGHT_MOTOR_FORWARD_PIN = 6
RIGHT_MOTOR_BACKWARD_PIN = 5

# Camera / control tuning
CAMERA_INDEX = int(os.environ.get("CAMERA_INDEX", "0"))
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
ROI_TOP_RATIO = 0.42

# RoboCup-like line follow behavior
BASE_SPEED = 0.42
KP_TURN = 0.95
MAX_TURN = 0.55
SEARCH_SPEED = 0.28
LINE_MIN_CONTOUR_AREA = 280
LOST_LINE_THRESHOLD_FRAMES = 40

# Green marker detection (HSV)
GREEN_MIN = np.array([40, 50, 35], dtype=np.uint8)
GREEN_MAX = np.array([90, 255, 255], dtype=np.uint8)
GREEN_MIN_CONTOUR_AREA = 220
MARKER_TOLERANCE_FROM_LINE = 20
MARKER_COOLDOWN_SEC = 1.1

# Black line detection (HSV)
BLACK_MIN = np.array([0, 0, 0], dtype=np.uint8)
BLACK_MAX = np.array([179, 255, 76], dtype=np.uint8)

# Marker action scripts: (left_speed, right_speed, duration_sec)
ACTION_SCRIPTS = {
    "left": [(0.28, 0.28, 0.20), (-0.48, 0.48, 0.34)],
    "right": [(0.28, 0.28, 0.20), (0.48, -0.48, 0.34)],
    "u_turn": [(0.00, 0.00, 0.08), (0.55, -0.55, 0.62), (-0.30, -0.30, 0.18)],
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


def detect_line_and_markers(frame):
    """
    Returns:
      line_center: (x, y) in full frame, or None
      black_mask: binary mask line ROI
      green_mask: binary mask green ROI
      marker_positions_x: list[int] green marker x positions in full frame
      roi_top: ROI start y
      line_cx_roi: line center x in ROI, or None
    """
    height, width = frame.shape[:2]
    roi_top = int(height * ROI_TOP_RATIO)
    roi = frame[roi_top:, :]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    green_mask = cv2.inRange(hsv, GREEN_MIN, GREEN_MAX)
    green_mask = _clean_mask(green_mask)

    black_mask = cv2.inRange(hsv, BLACK_MIN, BLACK_MAX)
    # Ignore green patches while following black line
    black_mask = cv2.bitwise_and(black_mask, cv2.bitwise_not(green_mask))
    black_mask = _clean_mask(black_mask)

    contours_line, _ = cv2.findContours(
        black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    line_center = None
    line_cx_roi = None

    if contours_line:
        largest = max(contours_line, key=cv2.contourArea)
        if cv2.contourArea(largest) >= LINE_MIN_CONTOUR_AREA:
            m_line = cv2.moments(largest)
            if m_line["m00"] > 0:
                cx = int(m_line["m10"] / m_line["m00"])
                cy = int(m_line["m01"] / m_line["m00"])
                line_cx_roi = cx
                line_center = (cx, cy + roi_top)

    marker_positions_x = []
    valid_green_contours = []
    contours_green, _ = cv2.findContours(
        green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    for cnt in contours_green:
        if cv2.contourArea(cnt) < GREEN_MIN_CONTOUR_AREA:
            continue
        mg = cv2.moments(cnt)
        if mg["m00"] == 0:
            continue
        gx = int(mg["m10"] / mg["m00"])
        marker_positions_x.append(gx)
        valid_green_contours.append(cnt)

    return line_center, black_mask, green_mask, marker_positions_x, roi_top, line_cx_roi, valid_green_contours


def decide_marker_action(green_positions, line_cx_roi):
    if line_cx_roi is None or not green_positions:
        return None, 0, 0

    left_count = 0
    right_count = 0
    for gx in green_positions:
        if gx < (line_cx_roi - MARKER_TOLERANCE_FROM_LINE):
            left_count += 1
        elif gx > (line_cx_roi + MARKER_TOLERANCE_FROM_LINE):
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
    pygame.display.set_caption("OivioPi RoboCup Line Follower")

    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        raise RuntimeError(
            f"Cannot open webcam index {CAMERA_INDEX}. Try CAMERA_INDEX=1."
        )

    running = True
    paused = False

    last_seen_x = None
    lost_line_counter = 0
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
                set_motor_speeds(-SEARCH_SPEED, SEARCH_SPEED)
                sleep(0.02)
                continue

            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            now = monotonic()
            (
                line_center,
                line_mask,
                green_mask,
                green_positions,
                roi_top,
                line_cx_roi,
                green_contours,
            ) = detect_line_and_markers(frame)

            frame_mid_x = frame.shape[1] // 2
            status = "IDLE"

            if paused:
                stop()
                status = "PAUSED"
                current_action = None
            else:
                # Continue marker action if one is active
                if tick_action(now):
                    status = f"MARKER_{current_action.upper()}"
                else:
                    # Trigger marker action if line exists and cooldown passed
                    marker_action, left_mk, right_mk = decide_marker_action(
                        green_positions, line_cx_roi
                    )
                    if marker_action and now >= marker_cooldown_until and line_center:
                        start_action(marker_action, now)
                        marker_cooldown_until = now + MARKER_COOLDOWN_SEC
                        last_seen_x = None
                        lost_line_counter = 0
                        status = f"MARKER_{marker_action.upper()} L{left_mk} R{right_mk}"
                    elif line_center is not None:
                        # Normal line following (P-control)
                        error = (line_center[0] - frame_mid_x) / float(frame_mid_x)
                        turn = clamp(KP_TURN * error, -MAX_TURN, MAX_TURN)
                        left_speed = BASE_SPEED + turn
                        right_speed = BASE_SPEED - turn
                        set_motor_speeds(left_speed, right_speed)
                        last_seen_x = line_center[0]
                        lost_line_counter = 0
                        status = f"TRACK err={error:+.2f}"
                    else:
                        # Lost line recovery
                        lost_line_counter += 1
                        if (
                            last_seen_x is not None
                            and lost_line_counter < LOST_LINE_THRESHOLD_FRAMES
                        ):
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
                frame, (0, roi_top), (frame.shape[1] - 1, frame.shape[0] - 1), (255, 0, 0), 2
            )
            cv2.line(
                frame, (frame_mid_x, roi_top), (frame_mid_x, frame.shape[0]), (255, 255, 0), 2
            )

            if line_center is not None:
                cv2.circle(frame, line_center, 6, (0, 255, 255), -1)

            for cnt in green_contours:
                cnt_shifted = cnt.copy()
                cnt_shifted[:, 0, 1] += roi_top
                cv2.drawContours(frame, [cnt_shifted], -1, (0, 255, 0), 2)

            for gx in green_positions:
                cv2.circle(frame, (gx, roi_top + 10), 6, (0, 255, 0), -1)

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
                f"Lost:{lost_line_counter} Green:{len(green_positions)}",
                (10, 46),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                (255, 255, 255),
                1,
            )

            cv2.imshow("OivioPi RoboCup Line Follower", frame)
            cv2.imshow("Line Mask", line_mask)
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
