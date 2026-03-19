import math
import os
from time import monotonic, sleep

import cv2
import numpy as np
import pygame
from gpiozero import Motor

try:
    from mpu6050 import mpu6050
except Exception:
    mpu6050 = None

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

# Line follow behavior
BASE_SPEED = float(os.environ.get("BASE_SPEED", "0.42"))
KP_TURN = float(os.environ.get("KP_TURN", "0.95"))
MAX_TURN = float(os.environ.get("MAX_TURN", "0.55"))
SEARCH_SPEED = float(os.environ.get("SEARCH_SPEED", "0.28"))
LINE_MIN_CONTOUR_AREA = int(os.environ.get("LINE_MIN_CONTOUR_AREA", "280"))
LOST_LINE_THRESHOLD_FRAMES = int(os.environ.get("LOST_LINE_THRESHOLD_FRAMES", "40"))

# Ramp behavior (IMU pitch)
RAMP_UP_PITCH_DEG = float(os.environ.get("RAMP_UP_PITCH_DEG", "10.0"))
RAMP_DOWN_PITCH_DEG = float(os.environ.get("RAMP_DOWN_PITCH_DEG", "-10.0"))
RAMP_UP_SPEED = float(os.environ.get("RAMP_UP_SPEED", "0.55"))
RAMP_DOWN_SPEED = float(os.environ.get("RAMP_DOWN_SPEED", "0.30"))
IMU_ALPHA = float(os.environ.get("IMU_ALPHA", "0.25"))
IMU_ADDR = int(os.environ.get("IMU_ADDR", "0x68"), 16)

# Red line stop behavior
RED_DETECT_RATIO = float(os.environ.get("RED_DETECT_RATIO", "0.28"))
RED_MIN_CONTOUR_AREA = int(os.environ.get("RED_MIN_CONTOUR_AREA", "900"))
RED_CONFIRM_FRAMES = int(os.environ.get("RED_CONFIRM_FRAMES", "3"))

# Black line detection (HSV)
BLACK_MIN = np.array([0, 0, 0], dtype=np.uint8)
BLACK_MAX = np.array([179, 255, 76], dtype=np.uint8)

# Red detection (HSV: low + high hue ranges)
RED1_MIN = np.array([0, 100, 80], dtype=np.uint8)
RED1_MAX = np.array([12, 255, 255], dtype=np.uint8)
RED2_MIN = np.array([165, 100, 80], dtype=np.uint8)
RED2_MAX = np.array([179, 255, 255], dtype=np.uint8)

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


def detect_red_line(frame):
    """
    Detect red strip near the bottom of image.
    Returns red_detected, red_mask, red_contour.
    """
    h, w = frame.shape[:2]
    red_top = int(h * (1.0 - RED_DETECT_RATIO))
    roi = frame[red_top:, :]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    mask1 = cv2.inRange(hsv, RED1_MIN, RED1_MAX)
    mask2 = cv2.inRange(hsv, RED2_MIN, RED2_MAX)
    red_mask = cv2.bitwise_or(mask1, mask2)
    red_mask = _clean_mask(red_mask)

    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False, red_mask, red_top, None

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < RED_MIN_CONTOUR_AREA:
        return False, red_mask, red_top, None

    return True, red_mask, red_top, largest


class IMUReader:
    def __init__(self, addr=0x68, alpha=0.25):
        self.alpha = alpha
        self.pitch_f = None
        self.ok = False
        self.sensor = None

        if mpu6050 is None:
            return

        try:
            self.sensor = mpu6050(addr)
            _ = self.sensor.get_accel_data()
            self.ok = True
        except Exception:
            self.sensor = None
            self.ok = False

    def read_pitch_deg(self):
        if not self.ok or self.sensor is None:
            return None
        try:
            acc = self.sensor.get_accel_data()
            ax, ay, az = acc["x"], acc["y"], acc["z"]
            pitch = math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))
            if self.pitch_f is None:
                self.pitch_f = pitch
            else:
                self.pitch_f = self.alpha * pitch + (1.0 - self.alpha) * self.pitch_f
            return self.pitch_f
        except Exception:
            return None


def main():
    pygame.init()
    pygame.display.set_mode((220, 120))  # Dummy window for keyboard events
    pygame.display.set_caption("OivioPi Ramp + Red Line Stop")

    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open webcam index {CAMERA_INDEX}. Try CAMERA_INDEX=1.")

    imu = IMUReader(addr=IMU_ADDR, alpha=IMU_ALPHA)

    running = True
    paused = False
    stopped_on_red = False

    last_seen_x = None
    lost_line_counter = 0
    red_confirm = 0

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
                    elif event.key == pygame.K_r:
                        # manual reset after red-line stop
                        stopped_on_red = False
                        red_confirm = 0

            ok, frame = cap.read()
            if not ok:
                stop()
                sleep(0.02)
                continue

            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            line_center, line_mask, roi_top, line_contour = detect_line(frame)
            red_detected, red_mask, red_top, red_contour = detect_red_line(frame)
            frame_mid_x = frame.shape[1] // 2

            pitch = imu.read_pitch_deg()
            ramp_state = "FLAT"
            target_base_speed = BASE_SPEED
            if pitch is not None:
                if pitch >= RAMP_UP_PITCH_DEG:
                    ramp_state = "UP"
                    target_base_speed = RAMP_UP_SPEED
                elif pitch <= RAMP_DOWN_PITCH_DEG:
                    ramp_state = "DOWN"
                    target_base_speed = RAMP_DOWN_SPEED

            status = "IDLE"

            if paused:
                stop()
                status = "PAUSED"
            elif stopped_on_red:
                stop()
                status = "RED_STOP"
            else:
                if red_detected:
                    red_confirm += 1
                else:
                    red_confirm = 0

                if red_confirm >= RED_CONFIRM_FRAMES:
                    stop()
                    stopped_on_red = True
                    status = "RED_STOP"
                elif line_center is not None:
                    error = (line_center[0] - frame_mid_x) / float(frame_mid_x)
                    turn = clamp(KP_TURN * error, -MAX_TURN, MAX_TURN)
                    left_speed = target_base_speed + turn
                    right_speed = target_base_speed - turn
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
            cv2.rectangle(frame, (0, roi_top), (frame.shape[1] - 1, frame.shape[0] - 1), (255, 0, 0), 2)
            cv2.line(frame, (frame_mid_x, roi_top), (frame_mid_x, frame.shape[0]), (255, 255, 0), 2)
            cv2.rectangle(frame, (0, red_top), (frame.shape[1] - 1, frame.shape[0] - 1), (0, 0, 255), 1)

            if line_contour is not None:
                cnt_shifted = line_contour.copy()
                cnt_shifted[:, 0, 1] += roi_top
                cv2.drawContours(frame, [cnt_shifted], -1, (0, 165, 255), 2)

            if red_contour is not None:
                red_shifted = red_contour.copy()
                red_shifted[:, 0, 1] += red_top
                cv2.drawContours(frame, [red_shifted], -1, (0, 0, 255), 2)

            if line_center is not None:
                cv2.circle(frame, line_center, 6, (0, 255, 255), -1)

            pitch_text = "N/A" if pitch is None else f"{pitch:+.1f}"
            cv2.putText(frame, status, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 255), 2)
            cv2.putText(
                frame,
                f"Pitch:{pitch_text} Ramp:{ramp_state} Base:{target_base_speed:.2f}",
                (10, 46),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (255, 255, 255),
                1,
            )
            cv2.putText(
                frame,
                f"RedDet:{int(red_detected)} Confirm:{red_confirm}/{RED_CONFIRM_FRAMES} (R=resume)",
                (10, 66),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (180, 180, 255),
                1,
            )

            cv2.imshow("OivioPi Ramp + Red Line Stop", frame)
            cv2.imshow("Line Mask", line_mask)
            cv2.imshow("Red Mask", red_mask)

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
