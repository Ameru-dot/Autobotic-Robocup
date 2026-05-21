import time

import motor
from mp_manager import motor_fl, motor_fr, motor_bl, motor_br, terminate, turn_brake_ms

MOTOR_TYPE = 2
UPLOAD_DATA = 1
MOTOR_PERIOD = 0.03

CONTROL_MAX = 255
SPEED_MAX = 1000
BRAKE_SETTLE_MS = 20

# Map logical wheels to Yahboom M1..M4 order.
# User mapping: M1 left, M2 left, M3 right, M4 right.
# Default assumption: M1=fl, M2=bl, M3=fr, M4=br.
MOTOR_ORDER = ("fl", "bl", "fr", "br")
MOTOR_INVERT = {"fl": False, "fr": False, "bl": False, "br": False}


def scale_speed(value: int) -> int:
    scaled = int(value * SPEED_MAX / CONTROL_MAX)
    return max(-SPEED_MAX, min(SPEED_MAX, scaled))


def init_driver():
    # Apply motor config once at startup (optional but matches Yahboom example)
    try:
        motor.MOTOR_TYPE = MOTOR_TYPE
        motor.send_upload_command(UPLOAD_DATA)
        time.sleep(0.1)
        motor.set_motor_parameter()
    except Exception:
        pass




def brake(pulse_ms: int = 30):
    pulse_ms = max(0, int(pulse_ms))
    try:
        # Pause telemetry uploads first so the stop pulse reaches the driver cleanly.
        motor.send_data("$upload:0,0,0#")
        motor.control_pwm(0, 0, 0, 0)
        if pulse_ms > 0:
            time.sleep(pulse_ms / 1000.0)
        motor.control_speed(0, 0, 0, 0)
        if BRAKE_SETTLE_MS > 0:
            time.sleep(BRAKE_SETTLE_MS / 1000.0)
    except Exception:
        pass

def motor_loop():
    init_driver()
    last_sent = (0, 0, 0, 0)
    last_send_time = 0.0
    while not terminate.value:
        now = time.time()
        desired = (motor_fl.value, motor_fr.value, motor_bl.value, motor_br.value)
        changed = desired != last_sent
        stale = (now - last_send_time) > MOTOR_PERIOD

        pulse_ms = int(turn_brake_ms.value)
        if pulse_ms > 0:
            turn_brake_ms.value = 0
            brake(pulse_ms)
            last_sent = (0, 0, 0, 0)
            last_send_time = time.time()
            continue

        if changed or stale:
            values = {"fl": desired[0], "fr": desired[1], "bl": desired[2], "br": desired[3]}
            ordered = []
            for key in MOTOR_ORDER:
                val = values[key]
                if MOTOR_INVERT.get(key, False):
                    val = -val
                ordered.append(val)
            scaled = tuple(scale_speed(v) for v in ordered)
            motor.control_speed(*scaled)
            last_sent = desired
            last_send_time = now

        time.sleep(0.005)

    try:
        motor.control_pwm(0, 0, 0, 0)
    except Exception:
        pass
