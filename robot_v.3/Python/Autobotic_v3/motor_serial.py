import time
import serial

from mp_manager import motor_fl, motor_fr, motor_bl, motor_br, terminate

# Arduino serial (L298N control)
ARDUINO_PORT = "/dev/ttyACM0"
ARDUINO_BAUD = 115200
SEND_PERIOD = 0.03

CONTROL_MAX = 255

# Logical wheel order to Arduino M1..M4
# M1=front left, M2=back left, M3=front right, M4=back right
MOTOR_ORDER = ("fl", "bl", "fr", "br")
MOTOR_INVERT = {"fl": False, "fr": False, "bl": False, "br": False}


def clamp_speed(value: int) -> int:
    return max(-CONTROL_MAX, min(CONTROL_MAX, int(value)))


def connect_serial():
    try:
        return serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=0.5)
    except serial.SerialException:
        return None


def motor_loop():
    ser = connect_serial()
    last_sent = (0, 0, 0, 0)
    last_send_time = 0.0

    while not terminate.value:
        if ser is None or not ser.is_open:
            time.sleep(1.0)
            ser = connect_serial()
            continue

        now = time.time()
        desired = (motor_fl.value, motor_fr.value, motor_bl.value, motor_br.value)
        changed = desired != last_sent
        stale = (now - last_send_time) > SEND_PERIOD

        if changed or stale:
            values = {"fl": desired[0], "fr": desired[1], "bl": desired[2], "br": desired[3]}
            ordered = []
            for key in MOTOR_ORDER:
                val = values[key]
                if MOTOR_INVERT.get(key, False):
                    val = -val
                ordered.append(clamp_speed(val))

            cmd = f"M,{ordered[0]},{ordered[1]},{ordered[2]},{ordered[3]}
"
            try:
                ser.write(cmd.encode())
            except serial.SerialException:
                try:
                    ser.close()
                except Exception:
                    pass
                ser = None

            last_sent = desired
            last_send_time = now

        time.sleep(0.005)

    try:
        if ser and ser.is_open:
            ser.write(b"M,0,0,0,0
")
            ser.close()
    except Exception:
        pass
