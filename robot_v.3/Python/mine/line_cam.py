import time
from multiprocessing import shared_memory

import cv2
import numpy as np

from Managers import ConfigManager
from mp_manager import (
    line_error_x,
    line_found,
    silver_prob,
    turn_direction,
    terminate,
    calibrate_color_status,
    calibration_color,
    exit_angle,
)

# Camera settings
CAM_INDEX = 1  # set to 0 or 1 depending on wiring
FRAME_W, FRAME_H = 448, 252
THRESHOLD = 70
MIN_AREA = 1200

# Green marker HSV ranges (tweak as needed)
GREEN_MIN = np.array([40, 50, 45])
GREEN_MAX = np.array([85, 255, 255])
# Threshold for black detection around marker
BLACK_THRESH = 125

# Red line HSV (exit line)
RED_MIN_1 = np.array([0, 100, 90])
RED_MAX_1 = np.array([10, 255, 255])
RED_MIN_2 = np.array([170, 100, 90])
RED_MAX_2 = np.array([180, 255, 255])

CONFIG_PATH = "config_mine.ini"
config_manager = ConfigManager(CONFIG_PATH)


def update_color_values():
    global GREEN_MIN, GREEN_MAX, THRESHOLD, RED_MIN_1, RED_MAX_1, RED_MIN_2, RED_MAX_2
    gmin = config_manager.read_variable("color_values_line", "green_min")
    gmax = config_manager.read_variable("color_values_line", "green_max")
    thr = config_manager.read_variable("line_params", "threshold")
    rmin1 = config_manager.read_variable("color_values_line", "red_min_1")
    rmax1 = config_manager.read_variable("color_values_line", "red_max_1")
    rmin2 = config_manager.read_variable("color_values_line", "red_min_2")
    rmax2 = config_manager.read_variable("color_values_line", "red_max_2")
    if gmin is not None:
        GREEN_MIN = np.array(gmin, dtype=np.uint8)
    if gmax is not None:
        GREEN_MAX = np.array(gmax, dtype=np.uint8)
    if thr is not None:
        try:
            THRESHOLD = int(thr)
        except Exception:
            pass
    if rmin1 is not None:
        RED_MIN_1 = np.array(rmin1, dtype=np.uint8)
    if rmax1 is not None:
        RED_MAX_1 = np.array(rmax1, dtype=np.uint8)
    if rmin2 is not None:
        RED_MIN_2 = np.array(rmin2, dtype=np.uint8)
    if rmax2 is not None:
        RED_MAX_2 = np.array(rmax2, dtype=np.uint8)


def find_line_error(frame_rgb):
    gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
    _, mask = cv2.threshold(gray, THRESHOLD, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return False, 0.0, mask, contours

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < MIN_AREA:
        return False, 0.0, mask, contours

    m = cv2.moments(largest)
    if m["m00"] == 0:
        return False, 0.0, mask, contours

    cx = int(m["m10"] / m["m00"])
    error_x = (cx - FRAME_W / 2) / (FRAME_W / 2)
    return True, error_x, mask, contours


def estimate_silver_prob(frame_rgb):
    # Simple brightness heuristic: ratio of very bright pixels
    gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
    bright = (gray > 230).astype(np.uint8)
    prob = bright.sum() / bright.size
    return float(prob)


def calibrate_color(frame_rgb):
    """
    Calibration: take center ROI, compute HSV min/max/percentiles, write to config.
    """
    roi = frame_rgb[int(FRAME_H * 0.25): int(FRAME_H * 0.75), int(FRAME_W * 0.25): int(FRAME_W * 0.75)]
    hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
    # Use percentiles for robustness
    h = hsv[:, :, 0].flatten()
    s = hsv[:, :, 1].flatten()
    v = hsv[:, :, 2].flatten()

    def band_from_mask(mask):
        if np.count_nonzero(mask) == 0:
            return None
        hh = h[mask]
        ss = s[mask]
        vv = v[mask]
        h_min = int(np.clip(np.percentile(hh, 2) - 5, 0, 180))
        h_max = int(np.clip(np.percentile(hh, 98) + 5, 0, 180))
        s_min = int(np.clip(np.percentile(ss, 2) - 10, 0, 255))
        s_max = int(np.clip(np.percentile(ss, 98) + 10, 0, 255))
        v_min = int(np.clip(np.percentile(vv, 2) - 10, 0, 255))
        v_max = int(np.clip(np.percentile(vv, 98) + 10, 0, 255))
        return [h_min, s_min, v_min], [h_max, s_max, v_max]

    if calibration_color.value == "line_green":
        res = band_from_mask(np.ones_like(h, dtype=bool))
        if res:
            min_arr, max_arr = res
            config_manager.write_variable("color_values_line", "green_min", min_arr)
            config_manager.write_variable("color_values_line", "green_max", max_arr)
    elif calibration_color.value == "line_black":
        # Use grayscale mean to set threshold
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        thr = int(max(0, min(255, np.mean(gray) - 20)))
        config_manager.write_variable("line_params", "threshold", thr)
    elif calibration_color.value == "line_red":
        # Split into two bands
        mask_low = h < 30
        mask_high = h > 150
        res_low = band_from_mask(mask_low)
        res_high = band_from_mask(mask_high)
        if res_low:
            mn, mx = res_low
            config_manager.write_variable("color_values_line", "red_min_1", mn)
            config_manager.write_variable("color_values_line", "red_max_1", mx)
        if res_high:
            mn, mx = res_high
            config_manager.write_variable("color_values_line", "red_min_2", mn)
            config_manager.write_variable("color_values_line", "red_max_2", mx)
    elif calibration_color.value == "zone_green":
        res = band_from_mask(np.ones_like(h, dtype=bool))
        if res:
            min_arr, max_arr = res
            config_manager.write_variable("color_values_zone", "green_min", min_arr)
            config_manager.write_variable("color_values_zone", "green_max", max_arr)
    elif calibration_color.value == "zone_red":
        mask_low = h < 30
        mask_high = h > 150
        res_low = band_from_mask(mask_low)
        res_high = band_from_mask(mask_high)
        if res_low:
            mn, mx = res_low
            config_manager.write_variable("color_values_zone", "red_min_1", mn)
            config_manager.write_variable("color_values_zone", "red_max_1", mx)
        if res_high:
            mn, mx = res_high
            config_manager.write_variable("color_values_zone", "red_min_2", mn)
            config_manager.write_variable("color_values_zone", "red_max_2", mx)

    update_color_values()
    calibrate_color_status.value = "none"


def check_green_markers(frame_rgb, mask_black):
    """
    Green marker heuristic adapted from main/line_cam.py:
    - Cari kontur hijau.
    - Semak hitam di atas/bawah/kiri/kanan marker untuk tentukan arah.
    """
    hsv = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2HSV)
    green_mask = cv2.inRange(hsv, GREEN_MIN, GREEN_MAX)
    contours, _ = cv2.findContours(green_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    black_dir = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area <= 2500:
            continue

        green_box = cv2.boxPoints(cv2.minAreaRect(contour))
        green_box = green_box[green_box[:, 1].argsort()]

        marker_height = green_box[-1][1] - green_box[0][1]
        black_dir.append(
            (
                int(green_box[2][1]),  # bottom y
                np.mean(mask_black[int(green_box[2][1]):np.minimum(int(green_box[2][1] + (marker_height * 0.8)), FRAME_H),
                                    np.minimum(int(green_box[2][0]), int(green_box[3][0])):np.maximum(int(green_box[2][0]), int(green_box[3][0]))]) if mask_black.size > 0 else 255,
                np.mean(mask_black[np.maximum(int(green_box[1][1] - (marker_height * 0.8)), 0):int(green_box[1][1]),
                                    np.minimum(np.maximum(int(green_box[0][0]), 0), np.maximum(int(green_box[1][0]), 0)):np.maximum(np.maximum(int(green_box[0][0]), 0), np.maximum(int(green_box[1][0]), 0))]) if mask_black.size > 0 else 255,
                # Left/right
                np.mean(mask_black[np.minimum(int(green_box[0][1]), int(green_box[1][1])):np.maximum(int(green_box[0][1]), int(green_box[1][1])),
                                    np.maximum(int(green_box[1][0] - (marker_height * 0.8)), 0):int(green_box[1][0])]) if mask_black.size > 0 else 255,
                np.mean(mask_black[np.minimum(int(green_box[2][1]), int(green_box[3][1])):np.maximum(int(green_box[2][1]), int(green_box[3][1])),
                                    int(green_box[2][0]):np.minimum(int(green_box[2][0] + (marker_height * 0.8)), FRAME_W)]) if mask_black.size > 0 else 255,
            )
        )

    turn_left = False
    turn_right = False
    left_bottom = False
    right_bottom = False

    for b in black_dir:
        bottom_y, mean_b, mean_t, mean_l, mean_r = b
        has_b = mean_b < BLACK_THRESH
        has_t = mean_t < BLACK_THRESH
        has_l = mean_l < BLACK_THRESH
        has_r = mean_r < BLACK_THRESH

        if has_t and has_l and not has_r:
            turn_right = True
            if bottom_y > FRAME_H * 0.95:
                right_bottom = True
        if has_t and has_r and not has_l:
            turn_left = True
            if bottom_y > FRAME_H * 0.95:
                left_bottom = True

    if turn_left and not turn_right:
        return "left"
    if turn_right and not turn_left:
        return "right"
    if turn_left and turn_right and not (left_bottom and right_bottom):
        return "turn_around"
    return "straight"


def line_cam_loop():
    update_color_values()
    shm_line = None
    shm_arr = None
    size = FRAME_W * FRAME_H * 3
    try:
        shm_line = shared_memory.SharedMemory(name="shm_line", create=True, size=size)
    except FileExistsError:
        shm_line = shared_memory.SharedMemory(name="shm_line")
    shm_arr = np.ndarray((FRAME_H, FRAME_W, 3), dtype=np.uint8, buffer=shm_line.buf)

    cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_V4L2)
    if not cap.isOpened():
        cap = cv2.VideoCapture(CAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
    time.sleep(0.1)

    try:
        while not terminate.value:
            ok, frame_bgr = cap.read()
            if not ok:
                time.sleep(0.03)
                continue
            if frame_bgr.shape[1] != FRAME_W or frame_bgr.shape[0] != FRAME_H:
                frame_bgr = cv2.resize(frame_bgr, (FRAME_W, FRAME_H))
            frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

            if calibrate_color_status.value == "calibrate":
                calibrate_color(frame)

            found, err, mask, contours = find_line_error(frame)
            line_found.value = found
            line_error_x.value = err
            silver_prob.value = estimate_silver_prob(frame)
            turn_direction.value = check_green_markers(frame, mask)

            # Overlay line contour and center
            if contours and found:
                largest = max(contours, key=cv2.contourArea)
                cv2.drawContours(frame, [largest], -1, (0, 255, 0), 2)
                m = cv2.moments(largest)
                if m["m00"] != 0:
                    cx = int(m["m10"] / m["m00"])
                    cy = int(m["m01"] / m["m00"])
                    cv2.line(frame, (cx, FRAME_H), (cx, int(FRAME_H * 0.7)), (0, 0, 255), 2)
                    cv2.circle(frame, (cx, cy), 3, (255, 0, 0), -1)

            # Overlay green marker mask (outline)
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            green_mask = cv2.inRange(hsv, GREEN_MIN, GREEN_MAX)
            green_contours, _ = cv2.findContours(green_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            for c in green_contours:
                if cv2.contourArea(c) > 1500:
                    box = cv2.boxPoints(cv2.minAreaRect(c))
                    box = np.intp(box)
                    cv2.drawContours(frame, [box], -1, (0, 0, 255), 2)

            # Detect red line (exit) and angle
            red_mask = cv2.inRange(hsv, RED_MIN_1, RED_MAX_1) + cv2.inRange(hsv, RED_MIN_2, RED_MAX_2)
            red_contours, _ = cv2.findContours(red_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            exit_found = False
            angle_exit = -181.0
            if len(red_contours) > 0:
                largest_red = max(red_contours, key=cv2.contourArea)
                if cv2.contourArea(largest_red) > 2000:
                    box = cv2.boxPoints(cv2.minAreaRect(largest_red))
                    box = np.intp(box)
                    cv2.drawContours(frame, [box], -1, (0, 0, 255), 2)
                    (center, (w, h), ang) = cv2.minAreaRect(largest_red)
                    # Normalize angle: lib returns -90..0; convert to -90..90
                    if w < h:
                        angle_exit = ang
                    else:
                        angle_exit = ang + 90
                    exit_found = True
            from mp_manager import red_line_detected  # local import to avoid circular deps
            red_line_detected.value = exit_found
            exit_angle.value = angle_exit

            # Write RGB frame to shared memory
            try:
                shm_arr[:] = frame
            except Exception:
                pass
    finally:
        cap.release()
        if shm_line:
            try:
                shm_line.close()
                shm_line.unlink()
            except Exception:
                pass
