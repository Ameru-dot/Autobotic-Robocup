#!/usr/bin/env python3
"""
Launcher that mirrors the original folder structure but uses the new hardware:
- RDK X5 + dual USB webcams (OpenCV /dev/video0,/dev/video2)
- Yahboom motor driver over USB serial
- Arduino serial for IMU/IR + servos
- Omni-wheel kinematics

Processes:
- line_cam_loop: writes line error to shared memory
- motor_serial.motor_loop: sends motor commands to Yahboom driver
- sensor_serial.serial_loop: reads IMU/IR, sends servo/LED commands to Arduino
- control.control_loop: reads line + telemetry and sets motor targets
"""

from multiprocessing import Process
import time

from line_cam import line_cam_loop
from zone_cam import zone_cam_loop
from motor_serial import motor_loop
from sensor_serial import serial_loop
from control import control_loop
from manual_control import manual_loop
from ui_tk import ui_loop
from mp_manager import terminate


def main():
    procs = [
        Process(target=line_cam_loop, name="line_cam"),
        Process(target=zone_cam_loop, name="zone_cam"),
        Process(target=motor_loop, name="motor"),
        Process(target=serial_loop, name="serial"),
        Process(target=control_loop, name="control"),
        Process(target=ui_loop, name="ui"),
        Process(target=manual_loop, name="manual"),
    ]

    for p in procs:
        p.start()

    try:
        while all(p.is_alive() for p in procs):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        terminate.value = True
        for p in procs:
            p.join()


if __name__ == "__main__":
    main()
