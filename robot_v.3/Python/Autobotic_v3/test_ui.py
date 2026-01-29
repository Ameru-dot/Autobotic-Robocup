#!/usr/bin/env python3
"""
Standalone UI test (no external deps on project state).
Shows the same layout as ui_tk but feeds dummy data.
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
import threading
import time


class DummyState:
    def __init__(self):
        self.t = 0.0
        self.status = "Testing UI"
        self.objective = "follow_line"
        self.line_found = True
        self.line_err = 0.0
        self.silver = 0.0
        self.turn_dir = "straight"
        self.exit_ang = 0.0
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        self.ir1 = 0
        self.ir2 = 0
        self.irb = 0
        self.ball_type = "none"
        self.ball_err = 0.0
        self.ball_conf = 0.0
        self.ball_width = 0.0
        self.zone_g_found = False
        self.zone_g_err = 0.0
        self.zone_r_found = False
        self.zone_r_err = 0.0
        self.alive = 0
        self.dead = 0
        self.running = True
        self.img1 = np.zeros((252, 448, 3), dtype=np.uint8)
        self.img2 = np.zeros((264, 640, 3), dtype=np.uint8)
        self.light_on = False

    def tick(self):
        while self.running:
            self.t += 0.2
            self.status = f"Testing UI t={self.t:.1f}"
            self.objective = "follow_line" if int(self.t) % 2 == 0 else "zone"
            self.line_found = int(self.t) % 3 != 0
            self.line_err = 0.3 * (1 if int(self.t) % 4 < 2 else -1)
            self.silver = 0.05 + 0.02 * (self.t % 1)
            self.turn_dir = "left" if int(self.t) % 3 == 0 else ("right" if int(self.t) % 3 == 1 else "straight")
            self.exit_ang = 30.0 if int(self.t) % 2 == 0 else -25.0
            self.yaw = (self.yaw + 5) % 360
            self.pitch = 1.0
            self.roll = -1.0
            self.ir1 = 500 + int(400 * ((self.t % 2)))
            self.ir2 = 400 + int(300 * ((self.t % 3) / 3))
            self.irb = 600 + int(200 * ((self.t % 4) / 4))
            self.ball_type = "silver" if int(self.t) % 2 == 0 else "black"
            self.ball_err = 0.2 * (1 if int(self.t) % 2 == 0 else -1)
            self.ball_conf = 0.6
            self.ball_width = 100 + 20 * (self.t % 2)
            self.zone_g_found = int(self.t) % 2 == 0
            self.zone_g_err = 0.1 * (1 if int(self.t) % 2 == 0 else -1)
            self.zone_r_found = int(self.t) % 3 == 0
            self.zone_r_err = -0.1
            self.alive = int(self.t) % 3
            self.dead = int(self.t) % 2
            self.light_on = int(self.t) % 2 == 0
            self.img1[:] = (int((self.t * 10) % 255), 50, 50)
            self.img2[:] = (50, int((self.t * 20) % 255), 50)
            time.sleep(0.2)


def build_ui(state: DummyState):
    root = tk.Tk()
    root.title("UI Test (Standalone)")
    root.geometry("1100x700")
    root.resizable(False, False)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("Title.TLabel", font=("Segoe UI", 12, "bold"))
    style.configure("Key.TLabel", font=("Segoe UI", 10, "bold"))
    style.configure("Val.TLabel", font=("Segoe UI", 10))

    root.columnconfigure(0, weight=0)
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)

    left = ttk.Frame(root, padding=10)
    left.grid(row=0, column=0, sticky="ns")

    right = ttk.Frame(root, padding=10)
    right.grid(row=0, column=1, sticky="nsew")
    right.columnconfigure(0, weight=1)

    labels = {k: tk.StringVar() for k in [
        "status",
        "objective",
        "line",
        "turn",
        "exit",
        "silver",
        "imu",
        "ir",
        "ball",
        "zone",
        "victim",
    ]}

    light_var = tk.StringVar(value="Light: OFF")

    def kv_row(frame, row, key, var):
        ttk.Label(frame, text=key, style="Key.TLabel").grid(row=row, column=0, sticky="w", padx=4, pady=2)
        ttk.Label(frame, textvariable=var, style="Val.TLabel").grid(row=row, column=1, sticky="w", padx=4, pady=2)

    system_frame = ttk.LabelFrame(left, text="System", padding=8)
    system_frame.grid(row=0, column=0, sticky="ew")
    kv_row(system_frame, 0, "Status", labels["status"])
    kv_row(system_frame, 1, "Objective", labels["objective"])

    light_label = tk.Label(system_frame, textvariable=light_var, fg="#fff", bg="#444", width=14)
    light_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=4, pady=4)

    line_frame = ttk.LabelFrame(left, text="Line", padding=8)
    line_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
    kv_row(line_frame, 0, "Line", labels["line"])
    kv_row(line_frame, 1, "Turn", labels["turn"])
    kv_row(line_frame, 2, "Exit Ang", labels["exit"])
    kv_row(line_frame, 3, "Silver", labels["silver"])

    imu_frame = ttk.LabelFrame(left, text="IMU", padding=8)
    imu_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
    kv_row(imu_frame, 0, "Yaw/Pitch/Roll", labels["imu"])

    ir_frame = ttk.LabelFrame(left, text="IR", padding=8)
    ir_frame.grid(row=3, column=0, sticky="ew", pady=(8, 0))
    kv_row(ir_frame, 0, "Sensors", labels["ir"])

    zone_frame = ttk.LabelFrame(left, text="Zone", padding=8)
    zone_frame.grid(row=4, column=0, sticky="ew", pady=(8, 0))
    kv_row(zone_frame, 0, "Ball", labels["ball"])
    kv_row(zone_frame, 1, "Corners", labels["zone"])

    victim_frame = ttk.LabelFrame(left, text="Victims", padding=8)
    victim_frame.grid(row=5, column=0, sticky="ew", pady=(8, 0))
    kv_row(victim_frame, 0, "Counts", labels["victim"])

    mode_frame = ttk.LabelFrame(left, text="Modes", padding=8)
    mode_frame.grid(row=6, column=0, sticky="ew", pady=(8, 0))
    ttk.Button(mode_frame, text="Line", command=lambda: state.__setattr__("objective", "follow_line")).grid(row=0, column=0, padx=4, pady=2)
    ttk.Button(mode_frame, text="Zone", command=lambda: state.__setattr__("objective", "zone")).grid(row=0, column=1, padx=4, pady=2)
    ttk.Button(mode_frame, text="Manual", command=lambda: state.__setattr__("objective", "manual")).grid(row=0, column=2, padx=4, pady=2)

    calib_frame = ttk.LabelFrame(left, text="Calibration", padding=8)
    calib_frame.grid(row=7, column=0, sticky="ew", pady=(8, 0))
    ttk.Button(calib_frame, text="Line Green", command=lambda: state.__setattr__("status", "Calib line green (l-gl)")).grid(row=0, column=0, padx=3, pady=2)
    ttk.Button(calib_frame, text="Line Black", command=lambda: state.__setattr__("status", "Calib line black (l-bn)")).grid(row=0, column=1, padx=3, pady=2)
    ttk.Button(calib_frame, text="Line Red", command=lambda: state.__setattr__("status", "Calib line red (l-rl)")).grid(row=0, column=2, padx=3, pady=2)
    ttk.Button(calib_frame, text="Zone Green", command=lambda: state.__setattr__("status", "Calib zone green (z-g)")).grid(row=1, column=0, padx=3, pady=2)
    ttk.Button(calib_frame, text="Zone Red", command=lambda: state.__setattr__("status", "Calib zone red (z-r)")).grid(row=1, column=1, padx=3, pady=2)
    ttk.Button(calib_frame, text="Check", command=lambda: state.__setattr__("status", "Check mode")).grid(row=1, column=2, padx=3, pady=2)

    action_frame = ttk.LabelFrame(left, text="Actions", padding=8)
    action_frame.grid(row=8, column=0, sticky="ew", pady=(8, 0))

    def toggle_light():
        state.light_on = not state.light_on
        state.status = f"Light {'ON' if state.light_on else 'OFF'}"

    ttk.Button(action_frame, text="Toggle Light", command=toggle_light).grid(row=0, column=0, padx=4, pady=2)

    def on_quit():
        state.running = False
        try:
            root.destroy()
        except Exception:
            pass

    ttk.Button(action_frame, text="Quit", command=on_quit).grid(row=0, column=1, padx=4, pady=2)

    cam_frame = ttk.LabelFrame(right, text="Cameras", padding=6)
    cam_frame.grid(row=0, column=0, sticky="nsew")
    cam_frame.columnconfigure(0, weight=1)
    cam_frame.rowconfigure(0, weight=1)
    cam_frame.rowconfigure(1, weight=1)

    cam1_label = tk.Label(cam_frame, text="Line Camera", bg="#222", fg="#ccc", width=64, height=18)
    cam1_label.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
    cam2_label = tk.Label(cam_frame, text="Zone Camera", bg="#333", fg="#ccc", width=64, height=18)
    cam2_label.grid(row=1, column=0, padx=6, pady=6, sticky="nsew")

    cam1_img = None
    cam2_img = None

    def refresh():
        nonlocal cam1_img, cam2_img
        labels["status"].set(state.status)
        labels["objective"].set(state.objective)
        labels["line"].set(f"{'found' if state.line_found else 'lost'} err={state.line_err:.2f}")
        labels["turn"].set(state.turn_dir)
        labels["exit"].set(f"{state.exit_ang:.1f}")
        labels["silver"].set(f"{state.silver:.3f}")
        labels["imu"].set(f"yaw={state.yaw:.1f} pitch={state.pitch:.1f} roll={state.roll:.1f}")
        labels["ir"].set(f"IR1={state.ir1} IR2={state.ir2} IRB={state.irb}")
        labels["ball"].set(f"{state.ball_type} err={state.ball_err:.2f} conf={state.ball_conf:.2f} w={state.ball_width:.0f}")
        labels["zone"].set(f"G:{state.zone_g_found} err={state.zone_g_err:.2f} | R:{state.zone_r_found} err={state.zone_r_err:.2f}")
        labels["victim"].set(f"Alive:{state.alive} Dead:{state.dead}")

        light_var.set("Light: ON" if state.light_on else "Light: OFF")
        light_label.configure(bg="#1b5e20" if state.light_on else "#444")

        img = Image.fromarray(state.img1)
        img = img.resize((520, 292))
        cam1_img = ImageTk.PhotoImage(img)
        cam1_label.configure(image=cam1_img, text="")

        img2 = Image.fromarray(state.img2)
        img2 = img2.resize((520, 292))
        cam2_img = ImageTk.PhotoImage(img2)
        cam2_label.configure(image=cam2_img, text="")

        root.after(200, refresh)

    refresh()
    return root


def main():
    state = DummyState()
    feeder = threading.Thread(target=state.tick, daemon=True)
    feeder.start()
    root = build_ui(state)
    try:
        root.mainloop()
    finally:
        state.running = False
        feeder.join(timeout=1.0)


if __name__ == "__main__":
    main()
