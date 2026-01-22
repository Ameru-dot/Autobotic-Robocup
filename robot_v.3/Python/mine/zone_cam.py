"""
Zone/ball camera process (camera index 0 by default).
Detects balls with YOLO model and publishes ball type/confidence + horizontal error.
Extend this with color detection for red/green markers if needed.
"""

import time
from multiprocessing import shared_memory

import cv2
import numpy as np
from ultralytics import YOLO

from Managers import ConfigManager
from mp_manager import (
    ball_type,
    ball_error_x,
    ball_conf,
    ball_box_width,
    terminate,
    calibrate_color_status,
    calibration_color,
    zone_green_found,
    zone_green_error_x,
    zone_red_found,
    zone_red_error_x,
)

# Camera settings
CAM_INDEX = 0
FRAME_W, FRAME_H = 640, 480

# Model path (YOLO .pt by default; swap to NCNN export when ready)
MODEL_PATH = "../../Ai/models/ball_zone_s/ball_detect_s.pt"

CONFIG_PATH = "config_mine.ini"
config_manager = ConfigManager(CONFIG_PATH)
GREEN_MIN = np.array([40, 50, 35])
GREEN_MAX = np.array([90, 255, 255])
RED_MIN_1 = np.array([0, 100, 70])
RED_MAX_1 = np.array([10, 255, 255])
RED_MIN_2 = np.array([170, 100, 70])
RED_MAX_2 = np.array([180, 255, 255])


def update_color_values():
    global GREEN_MIN, GREEN_MAX, RED_MIN_1, RED_MAX_1, RED_MIN_2, RED_MAX_2
    gmin = config_manager.read_variable("color_values_zone", "green_min")
    gmax = config_manager.read_variable("color_values_zone", "green_max")
    rmin1 = config_manager.read_variable("color_values_zone", "red_min_1")
    rmax1 = config_manager.read_variable("color_values_zone", "red_max_1")
    rmin2 = config_manager.read_variable("color_values_zone", "red_min_2")
    rmax2 = config_manager.read_variable("color_values_zone", "red_max_2")
    if gmin is not None:
        GREEN_MIN = np.array(gmin, dtype=np.uint8)
    if gmax is not None:
        GREEN_MAX = np.array(gmax, dtype=np.uint8)
    if rmin1 is not None:
        RED_MIN_1 = np.array(rmin1, dtype=np.uint8)
    if rmax1 is not None:
        RED_MAX_1 = np.array(rmax1, dtype=np.uint8)
    if rmin2 is not None:
        RED_MIN_2 = np.array(rmin2, dtype=np.uint8)
    if rmax2 is not None:
        RED_MAX_2 = np.array(rmax2, dtype=np.uint8)


def calibrate_zone_color(frame_rgb):
    roi = frame_rgb[int(FRAME_H * 0.25): int(FRAME_H * 0.75), int(FRAME_W * 0.25): int(FRAME_W * 0.75)]
    hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
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

    if calibration_color.value == "zone_green":
        res = band_from_mask(np.ones_like(h, dtype=bool))
        if res:
            mn, mx = res
            config_manager.write_variable("color_values_zone", "green_min", mn)
            config_manager.write_variable("color_values_zone", "green_max", mx)
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

def zone_cam_loop():
    update_color_values()
    try:
        model = YOLO(MODEL_PATH, task="detect")
    except Exception:
        model = None
    shm_zone = None
    shm_arr = None
    size = FRAME_W * FRAME_H * 3
    try:
        shm_zone = shared_memory.SharedMemory(name="shm_zone", create=True, size=size)
    except FileExistsError:
        shm_zone = shared_memory.SharedMemory(name="shm_zone")
    shm_arr = np.ndarray((FRAME_H, FRAME_W, 3), dtype=np.uint8, buffer=shm_zone.buf)

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
                calibrate_zone_color(frame)
            else:
                # Zone color detection
                hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
                green_mask = cv2.inRange(hsv, GREEN_MIN, GREEN_MAX)
                red_mask = cv2.inRange(hsv, RED_MIN_1, RED_MAX_1) + cv2.inRange(hsv, RED_MIN_2, RED_MAX_2)

                def detect_offset(mask):
                    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                    if len(contours) > 0:
                        largest = max(contours, key=cv2.contourArea)
                        if cv2.contourArea(largest) > 2000:
                            x, y, w, h = cv2.boundingRect(largest)
                            cx = x + w // 2
                            err = (cx - FRAME_W / 2) / (FRAME_W / 2)
                            return True, err, (x, y, w, h)
                    return False, 0.0, None

                g_found, g_err, g_box = detect_offset(green_mask)
                r_found, r_err, r_box = detect_offset(red_mask)

                zone_green_found.value = g_found
                zone_green_error_x.value = g_err
                zone_red_found.value = r_found
                zone_red_error_x.value = r_err

                if g_box:
                    x, y, w, h = g_box
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if r_box:
                    x, y, w, h = r_box
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                # Ball detection
                if model is not None:
                    try:
                        results = model.predict(frame, imgsz=(512, 224), conf=0.3, iou=0.2, agnostic_nms=True, verbose=False)
                        result = results[0].numpy()
                        if len(result.boxes) > 0:
                            best = max(result.boxes, key=lambda b: float(b.conf[0]))
                            x1, y1, x2, y2 = best.xyxy[0].astype(int)
                            cx = int((x1 + x2) / 2)
                            width = x2 - x1
                            error_x = (cx - FRAME_W / 2) / (FRAME_W / 2)
                            cls_id = int(best.cls[0])
                            name = result.names[cls_id].lower()
                            ball_type.value = "silver" if "silver" in name or "alive" in name else ("black" if "black" in name or "dead" in name else "unknown")
                            ball_conf.value = float(best.conf[0])
                            ball_error_x.value = error_x
                            ball_box_width.value = float(width)
                            # Draw box
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 0), 2)
                            cv2.putText(frame, f"{name}:{ball_conf.value:.2f}", (x1, max(0, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1, cv2.LINE_AA)
                        else:
                            ball_type.value = "none"
                            ball_conf.value = 0.0
                            ball_error_x.value = 0.0
                            ball_box_width.value = 0.0
                    except Exception:
                        pass

            time.sleep(0.03)
            # Write RGB frame to shared memory (with overlays)
            try:
                shm_arr[:] = frame
            except Exception:
                pass
    finally:
        cap.release()
        if shm_zone:
            try:
                shm_zone.close()
                shm_zone.unlink()
            except Exception:
                pass
