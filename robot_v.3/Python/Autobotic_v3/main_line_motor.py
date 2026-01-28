#!/usr/bin/env python3
"""
Follow-line only launcher (no Arduino, no zone camera).
Starts:
- line_cam.py (line detection)
- control.py (follow-line control)
- motor_serial.py (Yahboom motor driver)
- ui_tk.py (optional, if DISPLAY)
"""

from multiprocessing import Process
import os
import time

from line_cam import line_cam_loop
from control import control_loop
from motor_serial import motor_loop
from ui_tk import ui_loop
from mp_manager import terminate, objective


def main():
    objective.value = "follow_line"

    procs = [
        Process(target=line_cam_loop, name="line_cam"),
        Process(target=control_loop, name="control"),
        Process(target=motor_loop, name="motor"),
    ]

    start_ui = os.environ.get("START_UI", "1") == "1" and bool(os.environ.get("DISPLAY"))
    if start_ui:
        procs.append(Process(target=ui_loop, name="ui"))

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
