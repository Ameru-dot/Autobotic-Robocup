import time
import serial

from mp_manager import (
    terminate,
    imu_yaw,
    imu_pitch,
    imu_roll,
    imu_last_ts,
    ir1,
    ir2,
    ir_back,
    ir_last_ts,
    motor_fl,
    motor_fr,
    motor_bl,
    motor_br,
    motor_last_set,
    status,
    light_on,
    servo_preset,
)

# Serial port settings
SERIAL_PORT = "/dev/ttyUSB0"
BAUD = 115200

# Motor send interval (seconds)
MOTOR_PERIOD = 0.03  # ~33 Hz


def parse_line(line: str):
    if line.startswith("IMU "):
        try:
            parts = line.split()
            yaw = float(parts[1].split(":")[1])
            pitch = float(parts[2].split(":")[1])
            roll = float(parts[3].split(":")[1])
            imu_yaw.value = yaw
            imu_pitch.value = pitch
            imu_roll.value = roll
            imu_last_ts.value = time.time()
        except Exception:
            pass
    elif line.startswith("IR1"):
        try:
            ir1.value = int(line.split()[1])
            ir_last_ts.value = time.time()
        except Exception:
            pass
    elif line.startswith("IR2"):
        try:
            ir2.value = int(line.split()[1])
            ir_last_ts.value = time.time()
        except Exception:
            pass
    elif line.startswith("IRB"):
        try:
            ir_back.value = int(line.split()[1])
            ir_last_ts.value = time.time()
        except Exception:
            pass


def send_motor_command(ser: serial.Serial, fl: int, fr: int, bl: int, br: int):
    ser.write(f"M {fl} {fr} {bl} {br}\n".encode("ascii"))

def send_led_command(ser: serial.Serial, on: bool):
    ser.write(f"LED {1 if on else 0}\n".encode("ascii"))

def send_servo_preset(ser: serial.Serial, preset_id: int):
    ser.write(f"SVP {preset_id}\n".encode("ascii"))


def serial_loop():
    last_sent = (0, 0, 0, 0)
    last_send_time = 0.0
    last_light = None
    last_servo_preset = -1

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=0.02)
        ser.reset_input_buffer()
        status.value = "Serial up"
    except Exception as e:
        status.value = f"Serial fail: {e}"
        # Wait and retry until terminate
        while not terminate.value:
            try:
                ser = serial.Serial(SERIAL_PORT, BAUD, timeout=0.02)
                ser.reset_input_buffer()
                status.value = "Serial up"
                break
            except Exception:
                time.sleep(1.0)
        else:
            return  # terminate flagged before connect
    while not terminate.value:
        # Read incoming
        try:
            line = ser.readline().decode(errors="ignore").strip()
            if line:
                parse_line(line)
        except Exception:
            pass

        # Send motor targets at fixed period or when changed
        now = time.time()
        desired = (motor_fl.value, motor_fr.value, motor_bl.value, motor_br.value)
        changed = desired != last_sent
        stale = (now - last_send_time) > MOTOR_PERIOD

        if changed or stale:
            send_motor_command(ser, *desired)
            last_sent = desired
            last_send_time = now

        # Send LED command if changed
        if last_light is None or light_on.value != last_light:
            try:
                send_led_command(ser, light_on.value)
                last_light = light_on.value
            except Exception:
                pass

        # Send servo preset if set
        if servo_preset.value >= 0 and servo_preset.value != last_servo_preset:
            try:
                send_servo_preset(ser, servo_preset.value)
                last_servo_preset = servo_preset.value
                servo_preset.value = -1
            except Exception:
                pass

    # On terminate
    try:
        ser.write(b"STOP\n")
    except Exception:
        pass
    try:
        ser.close()
    except Exception:
        pass
