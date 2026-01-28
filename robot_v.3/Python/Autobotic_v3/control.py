import math
import time

from mp_manager import (
    line_found,
    line_error_x,
    silver_prob,
    turn_direction,
    imu_last_ts,
    imu_yaw,
    imu_pitch,
    ball_type,
    ball_error_x,
    ball_conf,
    ball_box_width,
    objective,
    manual_vx,
    manual_vy,
    manual_omega,
    servo_preset,
    ir1,
    ir2,
    ir_back,
    red_line_detected,
    exit_angle,
    terminate,
    set_motor_targets,
    status,
    calibrate_color_status,
    calibration_color,
    light_on,
    zone_green_found,
    zone_green_error_x,
    zone_red_found,
    zone_red_error_x,
    alive_count,
    dead_count,
    zone_status,
)

# Motion tuning
KP_TURN = 220        # steering gain (scaled later)
VY_CMD = 0.35        # forward component 0..1
VX_CMD = 0.0         # lateral component
LOST_LINE_OMEGA = 0  # yaw when line lost (set small value to spin)
IMU_TIMEOUT = 2.0    # seconds before we slow due to stale IMU

# Heading hold when line lost
YAW_HOLD_GAIN = 0.8  # adjust how aggressively to return to last heading

# Zone/ball tuning
KP_BALL = 140        # steering gain when centering on ball
VY_ZONE = 0.2        # forward speed in zone
ZONE_SEARCH_OMEGA = 0.2  # rad/s approx (normalized scale)
BALL_CONF_MIN = 0.3
KX_BALL = 0.8        # strafe gain for ball centering
BALL_ALIGN_ERR = 0.05
BALL_WIDTH_THRESH = 80
VY_APPROACH = 0.12
VY_CLOSE = 0.22
KZ_ZONE = 0.6        # strafe gain for zone drop alignment
IR_FRONT_DROP = 700
IR_BACK_DROP = 700
TURN180_TIME = 1.0
BACK_TIME = 1.0
# Speed scaling on turns
TURN_SPEED_GAIN = 0.7
MIN_SPEED_SCALE = 0.25

# Intersection turn handling
TURN_FORWARD_TIME = 0.2
TURN_MIN_TIME = 0.25
TURN_MAX_TIME = 1.6
TURN_COOLDOWN = 0.8
TURN_FORWARD_SPEED = 0.2
TURN_OMEGA = 0.8
TURN_AROUND_OMEGA = 0.9
TURN_REACQUIRE_ERR = 0.2
TURN_USE_IMU = True
TURN_ANGLE_DEG = 90.0
TURN_IMU_TOL = 8.0
IMU_YAW_SIGN = 1.0

# Gap detection
GAP_LOST_TIME = 0.4
GAP_MAX_TIME = 1.2
GAP_SPEED = 0.18

# Ramp detection (using pitch)
RAMP_UP_PITCH = 10.0
RAMP_DOWN_PITCH = -10.0
RAMP_SPEED_UP = 0.2
RAMP_SPEED_DOWN = 0.15

# Omni geometry
WHEEL_ANGLES_DEG = {"fl": 45, "fr": -45, "bl": 135, "br": -135}
ROBOT_RADIUS = 0.12

# IR thresholds (raw ADC); adjust to your sensors
IR_BLOCK = 900
SILVER_TRIGGER = 0.08  # fraction of bright pixels to treat as silver strip
STOP_ON_RED = True     # stop when red line detected
EXIT_ANGLE_TOL = 20.0

# Light control per mode
LIGHT_AUTO = True


def mix_omni(vx: float, vy: float, omega: float):
    ang = {k: math.radians(v) for k, v in WHEEL_ANGLES_DEG.items()}
    raw = {
        "fl": -math.sin(ang["fl"]) * vx + math.cos(ang["fl"]) * vy + ROBOT_RADIUS * omega,
        "fr": -math.sin(ang["fr"]) * vx + math.cos(ang["fr"]) * vy + ROBOT_RADIUS * omega,
        "bl": -math.sin(ang["bl"]) * vx + math.cos(ang["bl"]) * vy + ROBOT_RADIUS * omega,
        "br": -math.sin(ang["br"]) * vx + math.cos(ang["br"]) * vy + ROBOT_RADIUS * omega,
    }
    max_mag = max(1.0, max(abs(v) for v in raw.values()))
    return {k: v / max_mag for k, v in raw.items()}


def control_loop():
    status.value = "Control running"
    last_line_seen = time.time()
    hold_heading = 0.0
    zone_state = "search"
    target_drop = "green"
    turn_end_time = 0.0
    back_end_time = 0.0
    gap_mode = False
    gap_start = 0.0
    turn_mode = None
    turn_start = 0.0
    turn_forward_end = 0.0
    turn_cooldown_until = 0.0
    last_turn_dir = "right"
    turn_start_yaw = 0.0
    while not terminate.value:
        # Calibration mode: freeze motors, set light on
        if calibrate_color_status.value != "none":
            light_on.value = True
            set_motor_targets(0, 0, 0, 0)
            status.value = f"Calibrating ({calibration_color.value})"
            time.sleep(0.05)
            continue
        elif LIGHT_AUTO:
            # Basic auto: light on during line/zone, off manual
            if objective.value in ["follow_line", "zone"]:
                light_on.value = True
            else:
                light_on.value = False

        # Obstacle check
        blocked = (ir1.value > IR_BLOCK) or (ir2.value > IR_BLOCK)

        # State machine
        if objective.value == "manual":
            omega = manual_omega.value
            vx = manual_vx.value
            vy = manual_vy.value
            status.value = f"Manual vx={vx:.2f} vy={vy:.2f} om={omega:.2f}"
        elif objective.value == "follow_line":
            if STOP_ON_RED and red_line_detected.value and (abs(exit_angle.value) < EXIT_ANGLE_TOL or exit_angle.value == -181.0):
                omega = 0.0
                vx = 0.0
                vy = 0.0
                status.value = f"Red line detected (stop) ang={exit_angle.value:.1f}"
                set_motor_targets(0, 0, 0, 0)
                time.sleep(0.02)
                continue

            now = time.time()
            if turn_mode is None and now >= turn_cooldown_until and turn_direction.value in ["left", "right", "turn_around"]:
                turn_mode = turn_direction.value
                turn_start = now
                turn_forward_end = now + TURN_FORWARD_TIME
                turn_cooldown_until = now + TURN_COOLDOWN
                turn_start_yaw = imu_yaw.value
                if turn_mode in ["left", "right"]:
                    last_turn_dir = turn_mode

            if turn_mode is not None:
                if now < turn_forward_end:
                    omega = 0.0
                    vx = 0.0
                    vy = TURN_FORWARD_SPEED
                else:
                    if turn_mode == "left":
                        omega = TURN_OMEGA
                    elif turn_mode == "right":
                        omega = -TURN_OMEGA
                    else:
                        omega = TURN_AROUND_OMEGA if last_turn_dir == "left" else -TURN_AROUND_OMEGA
                    vx = 0.0
                    vy = 0.0
                    imu_ready = TURN_USE_IMU and (now - imu_last_ts.value) < IMU_TIMEOUT
                    imu_done = False
                    if imu_ready:
                        delta = ((imu_yaw.value - turn_start_yaw + 540.0) % 360.0 - 180.0) * IMU_YAW_SIGN
                        if turn_mode == "left":
                            imu_done = abs(delta - TURN_ANGLE_DEG) <= TURN_IMU_TOL
                        elif turn_mode == "right":
                            imu_done = abs(delta + TURN_ANGLE_DEG) <= TURN_IMU_TOL
                        else:
                            imu_done = abs(abs(delta) - 180.0) <= TURN_IMU_TOL

                    if (now - turn_start) > TURN_MIN_TIME:
                        if imu_done:
                            turn_mode = None
                        elif line_found.value and abs(line_error_x.value) < TURN_REACQUIRE_ERR:
                            turn_mode = None
                    if (now - turn_start) > TURN_MAX_TIME:
                        turn_mode = None
                status.value = f"Turn {turn_mode}"
                speeds = mix_omni(vx, vy, omega)
                fl = int(255 * speeds["fl"])
                fr = int(255 * speeds["fr"])
                bl = int(255 * speeds["bl"])
                br = int(255 * speeds["br"])
                set_motor_targets(fl, fr, bl, br)
                time.sleep(0.02)
                continue

            if line_found.value and not blocked:
                turn_bias = 0.0
                if turn_direction.value == "left":
                    turn_bias = 20.0 / 255.0
                elif turn_direction.value == "right":
                    turn_bias = -20.0 / 255.0
                elif turn_direction.value == "turn_around":
                    turn_bias = 0.0  # let silver trigger handle state change if desired

                omega = -line_error_x.value * (KP_TURN / 255.0) + turn_bias
                vx = VX_CMD
                # Speed scaling on turns
                scale = max(MIN_SPEED_SCALE, 1.0 - abs(line_error_x.value) * TURN_SPEED_GAIN)
                vy = VY_CMD * scale
                status.value = f"Line: err {line_error_x.value:.2f} scale={scale:.2f}"
                last_line_seen = time.time()
                hold_heading = imu_yaw.value
                gap_mode = False
            else:
                if (time.time() - imu_last_ts.value) < IMU_TIMEOUT:
                    yaw_err = (hold_heading - imu_yaw.value + 540.0) % 360.0 - 180.0
                    omega = (yaw_err / 90.0) * YAW_HOLD_GAIN
                else:
                    omega = LOST_LINE_OMEGA
                vx = 0.0
                # Gap handling: if line lost recently, keep moving forward slowly
                if not blocked and (time.time() - last_line_seen) > GAP_LOST_TIME:
                    gap_mode = True
                    gap_start = last_line_seen
                if gap_mode and (time.time() - gap_start) < GAP_MAX_TIME:
                    vy = GAP_SPEED
                    status.value = "Gap mode"
                else:
                    vy = 0.0 if blocked else VY_CMD * 0.2
                    gap_mode = False
                    status.value = "Blocked (IR)" if blocked else "Searching line"

            # Trigger zone mode on silver prob (set in line_cam via brightness)
            if silver_prob.value > SILVER_TRIGGER:
                objective.value = "zone"
                status.value = "Silver detected -> zone"

        else:  # zone modes
            if zone_state in ["search", "approach"]:
                zone_status.value = "find_balls"
            elif zone_state == "pick_prep":
                zone_status.value = "pickup_ball"
            elif zone_state in ["go_drop", "dump_prep", "dump_back", "dump"]:
                zone_status.value = "deposit_green" if target_drop == "green" else "deposit_red"
            elif zone_state == "exit":
                zone_status.value = "exit"
            if blocked:
                omega = 0.0
                vx = 0.0
                vy = 0.0
                status.value = "Blocked (IR) zone"
            else:
                # Zone state machine (strafe approach + pick/dump)
                if zone_state == "search":
                    omega = ZONE_SEARCH_OMEGA
                    vx = 0.0
                    vy = 0.0
                    status.value = "Zone search"
                    if ball_type.value != "none" and ball_conf.value >= BALL_CONF_MIN:
                        zone_state = "approach"

                elif zone_state == "approach":
                    omega = 0.0
                    vx = KX_BALL * ball_error_x.value
                    vy = VY_APPROACH
                    status.value = f"Approach ball err={ball_error_x.value:.2f}"
                    if abs(ball_error_x.value) < BALL_ALIGN_ERR and ball_box_width.value > BALL_WIDTH_THRESH:
                        zone_state = "pick_prep"

                elif zone_state == "pick_prep":
                    omega = 0.0
                    vx = 0.0
                    vy = 0.0
                    status.value = "Picking"
                    servo_preset.value = 1  # lower_arm
                    time.sleep(0.4)
                    servo_preset.value = 2  # raise_arm_left
                    time.sleep(0.4)
                    if ball_type.value == "silver":
                        alive_count.value += 1
                        target_drop = "green"
                    else:
                        dead_count.value += 1
                        target_drop = "red"
                    zone_state = "go_drop"

                elif zone_state == "go_drop":
                    if target_drop == "green":
                        err = zone_green_error_x.value
                        found = zone_green_found.value
                    else:
                        err = zone_red_error_x.value
                        found = zone_red_found.value

                    if found:
                        vx = KZ_ZONE * err
                        omega = 0.0
                        vy = VY_ZONE
                        status.value = f"Drop {target_drop} err={err:.2f}"
                        if ir1.value < IR_FRONT_DROP or ir2.value < IR_FRONT_DROP:
                            zone_state = "dump_prep"
                            turn_end_time = time.time() + TURN180_TIME
                    else:
                        vx = 0.0
                        vy = 0.0
                        omega = ZONE_SEARCH_OMEGA
                        status.value = f"Searching drop {target_drop}"

                elif zone_state == "dump_prep":
                    vx = 0.0
                    vy = 0.0
                    omega = 0.8  # turn around
                    status.value = "Dump prep turn"
                    if time.time() > turn_end_time:
                        zone_state = "dump_back"
                        back_end_time = time.time() + BACK_TIME

                elif zone_state == "dump_back":
                    omega = 0.0
                    vx = 0.0
                    vy = -VY_APPROACH
                    status.value = "Dump back up"
                    if ir_back.value > 0 and ir_back.value < IR_BACK_DROP:
                        zone_state = "dump"
                    elif time.time() > back_end_time:
                        zone_state = "dump"

                elif zone_state == "dump":
                    omega = 0.0
                    vx = 0.0
                    vy = 0.0
                    status.value = f"Dumping to {target_drop}"
                    if target_drop == "green":
                        servo_preset.value = 4  # open gate1
                        time.sleep(0.3)
                        servo_preset.value = 5  # close gate1
                    else:
                        servo_preset.value = 6  # open gate2
                        time.sleep(0.3)
                        servo_preset.value = 7  # close gate2
                    if alive_count.value < 2 or dead_count.value < 1:
                        zone_state = "search"
                    else:
                        zone_state = "exit"

                elif zone_state == "exit":
                    omega = ZONE_SEARCH_OMEGA
                    vx = 0.0
                    vy = 0.0
                    status.value = "Zone exit"
                    if red_line_detected.value or line_found.value:
                        objective.value = "follow_line"
                        zone_state = "search"
                        target_drop = "green"

        # IMU stale -> slow down
        if (time.time() - imu_last_ts.value) > IMU_TIMEOUT:
            vy *= 0.5
            status.value += " (IMU stale)"

        speeds = mix_omni(vx, vy, omega)
        fl = int(255 * speeds["fl"])
        fr = int(255 * speeds["fr"])
        bl = int(255 * speeds["bl"])
        br = int(255 * speeds["br"])
        set_motor_targets(fl, fr, bl, br)

        time.sleep(0.02)

    # On terminate
    set_motor_targets(0, 0, 0, 0)
