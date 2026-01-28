#!/usr/bin/env python3
"""
Standalone UI test (no external deps on project state).
Shows the same layout as ui_tk but feeds dummy data (including zone offsets, IRB, victim counts).
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
        # Dummy images
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
            # Update dummy images (gradient)
            self.img1[:] = (int((self.t * 10) % 255), 50, 50)
            self.img2[:] = (50, int((self.t * 20) % 255), 50)
            time.sleep(0.2)


def build_ui(state: DummyState):
    root = tk.Tk()
    root.title("UI Test (Standalone)")
    root.geometry("960x620")
    root.resizable(False, False)

    labels = {k: tk.StringVar() for k in ["status", "objective", "line", "silver", "imu", "ir", "ball", "turn_dir", "zone", "victim"]}

    ttk.Label(root, text="Status").grid(row=0, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["status"]).grid(row=0, column=1, sticky="w")

    ttk.Label(root, text="Objective").grid(row=1, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["objective"]).grid(row=1, column=1, sticky="w")

    ttk.Label(root, text="Line").grid(row=2, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["line"]).grid(row=2, column=1, sticky="w")

    ttk.Label(root, text="Turn").grid(row=3, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["turn_dir"]).grid(row=3, column=1, sticky="w")

    ttk.Label(root, text="Silver").grid(row=4, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["silver"]).grid(row=4, column=1, sticky="w")

    ttk.Label(root, text="IMU").grid(row=5, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["imu"]).grid(row=5, column=1, sticky="w")

    ttk.Label(root, text="IR").grid(row=6, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["ir"]).grid(row=6, column=1, sticky="w")

    ttk.Label(root, text="Ball").grid(row=7, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["ball"]).grid(row=7, column=1, sticky="w")

    ttk.Label(root, text="Zone").grid(row=8, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["zone"]).grid(row=8, column=1, sticky="w")

    ttk.Label(root, text="Victims").grid(row=9, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["victim"]).grid(row=9, column=1, sticky="w")

    # Mode buttons
    btn_frame = ttk.Frame(root)
    btn_frame.grid(row=10, column=0, columnspan=2, pady=8)
    ttk.Button(btn_frame, text="Mode: Line", command=lambda: state.__setattr__("objective", "follow_line")).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="Mode: Zone", command=lambda: state.__setattr__("objective", "zone")).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="Mode: Manual", command=lambda: state.__setattr__("objective", "manual")).pack(side="left", padx=4)

    # Calibration buttons (dummy)
    calib_frame = ttk.Frame(root)
    calib_frame.grid(row=11, column=0, columnspan=2, pady=8)
    ttk.Button(calib_frame, text="Calib Line Green", command=lambda: state.__setattr__("status", "Calib line green (l-gl)")).pack(side="left", padx=2)
    ttk.Button(calib_frame, text="Calib Line Black", command=lambda: state.__setattr__("status", "Calib line black (l-bn)")).pack(side="left", padx=2)
    ttk.Button(calib_frame, text="Calib Line Red", command=lambda: state.__setattr__("status", "Calib line red (l-rl)")).pack(side="left", padx=2)
    ttk.Button(calib_frame, text="Calib Zone Green", command=lambda: state.__setattr__("status", "Calib zone green (z-g)")).pack(side="left", padx=2)
    ttk.Button(calib_frame, text="Calib Zone Red", command=lambda: state.__setattr__("status", "Calib zone red (z-r)")).pack(side="left", padx=2)
    ttk.Button(calib_frame, text="Check", command=lambda: state.__setattr__("status", "Check mode")).pack(side="left", padx=2)

    # Light toggle (dummy)
    def toggle_light():
        state.light_on = not state.light_on
        state.status = f"Light {'ON' if state.light_on else 'OFF'}"
    light_btn = ttk.Button(root, text="Toggle Light", command=toggle_light)
    light_btn.grid(row=12, column=0, columnspan=2, pady=6)

    # Camera placeholders
    cam_frame = ttk.Frame(root, borderwidth=1, relief="groove")
    cam_frame.grid(row=0, column=2, rowspan=16, padx=8, pady=8, sticky="nsew")
    cam_frame.grid_columnconfigure(0, weight=1)
    cam_frame.grid_rowconfigure(0, weight=1)
    cam_frame.grid_rowconfigure(1, weight=1)

    cam1_label = tk.Label(cam_frame, text="Camera 1\n(Line)", bg="#222", fg="#ccc", width=48, height=12, bd=2, relief="sunken", compound="center")
    cam1_label.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")
    cam2_label = tk.Label(cam_frame, text="Camera 2\n(Zone)", bg="#333", fg="#ccc", width=48, height=12, bd=2, relief="sunken", compound="center")
    cam2_label.grid(row=1, column=0, padx=4, pady=4, sticky="nsew")

    cam1_img = None
    cam2_img = None

    def refresh():
        nonlocal cam1_img, cam2_img
        labels["status"].set(state.status)
        labels["objective"].set(state.objective)
        labels["line"].set(f"{'found' if state.line_found else 'lost'} err={state.line_err:.2f}")
        labels["turn_dir"].set(state.turn_dir)
        labels["silver"].set(f"{state.silver:.3f}")
        labels["imu"].set(f"yaw={state.yaw:.1f} pitch={state.pitch:.1f} roll={state.roll:.1f}")
        labels["ir"].set(f"IR1={state.ir1} IR2={state.ir2} IRB={state.irb}")
        labels["ball"].set(f"{state.ball_type} err={state.ball_err:.2f} conf={state.ball_conf:.2f} w={state.ball_width:.0f}")
        labels["zone"].set(f"G:{state.zone_g_found} err={state.zone_g_err:.2f} | R:{state.zone_r_found} err={state.zone_r_err:.2f}")
        labels["victim"].set(f"Alive:{state.alive} Dead:{state.dead}")

        img = Image.fromarray(state.img1)
        img = img.resize((480, 270))
        cam1_img = ImageTk.PhotoImage(img)
        cam1_label.configure(image=cam1_img, text="Camera 1\n(Line)", compound="center")

        img2 = Image.fromarray(state.img2)
        img2 = img2.resize((480, 270))
        cam2_img = ImageTk.PhotoImage(img2)
        cam2_label.configure(image=cam2_img, text="Camera 2\n(Zone)", compound="center")

        root.after(200, refresh)

    def on_quit():
        state.running = False
        try:
            root.destroy()
        except Exception:
            pass

    quit_btn = ttk.Button(root, text="Quit", command=on_quit)
    quit_btn.grid(row=14, column=0, columnspan=2, pady=12)

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
