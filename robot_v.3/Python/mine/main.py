#!/usr/bin/env python3
"""
Launcher that mirrors the original folder structure but uses the new hardware:
- RDK X5 + dual CSI cameras (V4L2/OpenCV)
- Arduino serial bridge (L298N/L982N, IMU/IR telemetry)
- Omni-wheel kinematics

Processes:
- line_cam_loop: writes line error to shared memory
- sensor_serial.serial_loop: reads IMU/IR, sends motor commands from shared targets
- control.control_loop: reads line + telemetry and sets motor targets
"""

from multiprocessing import Process
import time

from line_cam import line_cam_loop
from zone_cam import zone_cam_loop
from sensor_serial import serial_loop
from control import control_loop
from manual_control import manual_loop
from ui_tk import ui_loop
from mp_manager import terminate


def main():
    procs = [
        Process(target=line_cam_loop, name="line_cam"),
        Process(target=zone_cam_loop, name="zone_cam"),
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
