import time
from multiprocessing import Manager

import numpy as np

from Managers import ConfigManager

config_manager = ConfigManager('config.ini')

manager = Manager()

# Global termination flag
terminate = manager.Value("b", False)

# Calibration flags
calibrate_color_status = manager.Value("s", "none")  # "none", "calibrate", "check"
calibration_color = manager.Value("s", "z-g")

# Line camera outputs (compat with yahboom control)
line_error_x = manager.Value("d", 0.0)   # -1..1
line_found = manager.Value("b", False)
turn_direction = manager.Value("s", "straight")  # "left", "right", "turn_around", "straight"
silver_prob = manager.Value("d", 0.0)  # 0..1

# Red line (exit) detection (compat)
red_line_detected = manager.Value("b", False)
exit_angle = manager.Value("d", -181.0)

# IMU (yaw/pitch/roll)
imu_yaw = manager.Value("d", 0.0)
imu_pitch = manager.Value("d", 0.0)
imu_roll = manager.Value("d", 0.0)
imu_last_ts = manager.Value("d", 0.0)

# IR sensors
ir1 = manager.Value("i", 0)
ir2 = manager.Value("i", 0)
ir_last_ts = manager.Value("d", 0.0)
ir_back = manager.Value("i", 0)

# Motor targets (to be sent to Yahboom driver)
motor_fl = manager.Value("i", 0)
motor_fr = manager.Value("i", 0)
motor_bl = manager.Value("i", 0)
motor_br = manager.Value("i", 0)
motor_last_set = manager.Value("d", 0.0)

# Status text
status = manager.Value("s", "Idle")

# Light control
light_on = manager.Value("b", False)

# Zone / ball detection (compat with yahboom control)
ball_type = manager.Value("s", "none")  # "silver" / "black" / "none"
ball_error_x = manager.Value("d", 0.0)  # -1..1 (relative horizontal error)
ball_conf = manager.Value("d", 0.0)
ball_box_width = manager.Value("d", 0.0)

# Objective / state machine
objective = manager.Value("s", "follow_line")  # "follow_line", "zone", "manual"

# Manual control targets (for manual mode)
manual_vx = manager.Value("d", 0.0)
manual_vy = manager.Value("d", 0.0)
manual_omega = manager.Value("d", 0.0)

# Servo commands (preset id; -1 means none)
servo_preset = manager.Value("i", -1)

# Zone targets (compat)
zone_green_found = manager.Value("b", False)
zone_green_error_x = manager.Value("d", 0.0)
zone_red_found = manager.Value("b", False)
zone_red_error_x = manager.Value("d", 0.0)

# Victim counts
alive_count = manager.Value("i", 0)
dead_count = manager.Value("i", 0)

# Main-style state used by full camera logic
rotation_y = manager.Value("s", "none")  # "ramp_up", "ramp_down", "none"
obstacle_direction = manager.Value("s", "n")
min_line_size = manager.Value("i", 3000)

line_angle = manager.Value("d", 0.0)
line_angle_y = manager.Value("i", -1)
line_detected = manager.Value("b", False)
line_crop = manager.Value("d", 0.6)
line_similarity = manager.Value("d", 0.0)
gap_angle = manager.Value("d", -181.0)
gap_center_x = manager.Value("i", -181)
gap_center_y = manager.Value("i", -1)
silver_angle = manager.Value("d", -181.0)
line_size = manager.Value("d", 0.0)
ramp_ahead = manager.Value("b", False)
red_detected = manager.Value("b", False)
turn_dir = manager.Value("s", "straight")
silver_value = manager.Value("d", -1.0)
black_average = manager.Value("d", 0.0)

ball_distance = manager.Value("i", 0)
ball_width = manager.Value("i", -1)
zone_similarity = manager.Value("d", 0.0)
zone_similarity_average = manager.Value("d", 0.0)
zone_found_black = manager.Value("b", False)
zone_found_green = manager.Value("b", False)
zone_found_red = manager.Value("b", False)
corner_distance = manager.Value("i", -181)
corner_size = manager.Value("i", 0)

capture_image = manager.Value("b", False)

line_status = manager.Value("s", "line_detected")
zone_status = manager.Value("s", "begin")


def set_motor_targets(fl: int, fr: int, bl: int, br: int):
    motor_fl.value = int(max(-255, min(255, fl)))
    motor_fr.value = int(max(-255, min(255, fr)))
    motor_bl.value = int(max(-255, min(255, bl)))
    motor_br.value = int(max(-255, min(255, br)))
    motor_last_set.value = time.time()


def empty_time_arr(length: int = 240):
    return np.zeros((length, 2))


def fill_array(value: int, length: int = 240, fill_time: int = 0):
    arr = np.zeros((length, 2))
    arr[fill_time:, 0] = time.perf_counter()
    arr[:, 1] = value
    return arr


def add_time_value(time_value_array, value):
    return np.delete(np.vstack((time_value_array, [time.perf_counter(), value])), 0, axis=0)


def get_time_average(time_value_array, time_range):
    time_value_array = time_value_array[np.where(time_value_array[:, 0] > time.perf_counter() - time_range)]
    if time_value_array.size > 0:
        return np.mean(time_value_array[:, 1])
    return -1


def get_max_value(time_value_array, time_range):
    time_value_array = time_value_array[np.where(time_value_array[:, 0] > time.perf_counter() - time_range)]
    return np.max(time_value_array[:, 1])


def calculate_x_offset(current_angle, target_angle):
    offset = target_angle - current_angle
    if offset > 180:
        offset -= 360
    elif offset < -180:
        offset += 360
    return offset


def find_average_color(image):
    avg_color_per_row = np.average(image, axis=0)
    avg_color = np.average(avg_color_per_row, axis=0)
    return avg_color
