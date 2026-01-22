import time

from motor import MotorDriver
from mp_manager import motor_fl, motor_fr, motor_bl, motor_br, terminate

MOTOR_PORT = "/dev/ttyUSB0"
MOTOR_BAUD = 115200
MOTOR_TYPE = 2
UPLOAD_DATA = 1
MOTOR_PERIOD = 0.03

CONTROL_MAX = 255
SPEED_MAX = 1000

# Map logical wheels to Yahboom M1..M4 order.
# User mapping: M1 left, M2 left, M3 right, M4 right.
# Default assumption: M1=fl, M2=bl, M3=fr, M4=br.
MOTOR_ORDER = ("fl", "bl", "fr", "br")
MOTOR_INVERT = {"fl": False, "fr": False, "bl": False, "br": False}


def scale_speed(value: int) -> int:
    scaled = int(value * SPEED_MAX / CONTROL_MAX)
    return max(-SPEED_MAX, min(SPEED_MAX, scaled))


def connect_driver() -> MotorDriver:
    return MotorDriver(
        port=MOTOR_PORT,
        baudrate=MOTOR_BAUD,
        motor_type=MOTOR_TYPE,
        upload_data=UPLOAD_DATA,
    )


def motor_loop():
    md = connect_driver()
    last_sent = (0, 0, 0, 0)
    last_send_time = 0.0
    while not terminate.value:
        if md.ser is None:
            time.sleep(1.0)
            md = connect_driver()
            continue

        now = time.time()
        desired = (motor_fl.value, motor_fr.value, motor_bl.value, motor_br.value)
        changed = desired != last_sent
        stale = (now - last_send_time) > MOTOR_PERIOD

        if changed or stale:
            values = {"fl": desired[0], "fr": desired[1], "bl": desired[2], "br": desired[3]}
            ordered = []
            for key in MOTOR_ORDER:
                val = values[key]
                if MOTOR_INVERT.get(key, False):
                    val = -val
                ordered.append(val)
            scaled = tuple(scale_speed(v) for v in ordered)
            md.control_speed(*scaled)
            last_sent = desired
            last_send_time = now

        time.sleep(0.005)

    try:
        md.control_speed(0, 0, 0, 0)
    except Exception:
        pass
    md.cleanup()
