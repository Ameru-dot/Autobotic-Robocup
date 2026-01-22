import time
from multiprocessing import Manager

manager = Manager()

# Global termination flag
terminate = manager.Value("b", False)

# Calibration flags
calibrate_color_status = manager.Value("s", "none")  # "none", "calibrate", "check"
calibration_color = manager.Value("s", "none")       # e.g., "line_green", "line_black", "zone_green", "zone_red"

# Line camera outputs
line_error_x = manager.Value("d", 0.0)   # -1..1
line_found = manager.Value("b", False)
turn_direction = manager.Value("s", "straight")  # "left", "right", "turn_around", "straight"

# Silver detection (simple brightness heuristic)
silver_prob = manager.Value("d", 0.0)  # 0..1

# Red line (exit) detection
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

# Motor targets (to be sent to Arduino)
motor_fl = manager.Value("i", 0)
motor_fr = manager.Value("i", 0)
motor_bl = manager.Value("i", 0)
motor_br = manager.Value("i", 0)
motor_last_set = manager.Value("d", 0.0)

# Status text
status = manager.Value("s", "Idle")

# Light control
light_on = manager.Value("b", False)

# Zone / ball detection
ball_type = manager.Value("s", "none")  # "silver" / "black" / "none"
ball_error_x = manager.Value("d", 0.0)  # -1..1 (relative horizontal error)
ball_conf = manager.Value("d", 0.0)
ball_box_width = manager.Value("d", 0.0)

# Objective / state machine
objective = manager.Value("s", "follow_line")  # "follow_line", "zone_search", "zone_approach"

# Manual control targets (for manual mode)
manual_vx = manager.Value("d", 0.0)
manual_vy = manager.Value("d", 0.0)
manual_omega = manager.Value("d", 0.0)

# Servo commands (preset id; -1 means none)
servo_preset = manager.Value("i", -1)

# Zone targets
zone_green_found = manager.Value("b", False)
zone_green_error_x = manager.Value("d", 0.0)
zone_red_found = manager.Value("b", False)
zone_red_error_x = manager.Value("d", 0.0)

# Victim counts
alive_count = manager.Value("i", 0)
dead_count = manager.Value("i", 0)


def set_motor_targets(fl: int, fr: int, bl: int, br: int):
    motor_fl.value = int(max(-255, min(255, fl)))
    motor_fr.value = int(max(-255, min(255, fr)))
    motor_bl.value = int(max(-255, min(255, bl)))
    motor_br.value = int(max(-255, min(255, br)))
    motor_last_set.value = time.time()
