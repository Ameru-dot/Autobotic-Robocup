import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
from multiprocessing import shared_memory

from mp_manager import (
    terminate,
    status,
    objective,
    calibrate_color_status,
    calibration_color,
    line_found,
    line_error_x,
    silver_prob,
    turn_direction,
    exit_angle,
    imu_yaw,
    imu_pitch,
    imu_roll,
    ir1,
    ir2,
    ir_back,
    ball_type,
    ball_error_x,
    ball_conf,
    ball_box_width,
    zone_green_found,
    zone_green_error_x,
    zone_red_found,
    zone_red_error_x,
    alive_count,
    dead_count,
    light_on,
)

LINE_SHM_NAME = "shm_line"
ZONE_SHM_NAME = "shm_zone"
LINE_SIZE = (448, 252)
ZONE_SIZE = (640, 264)


def attach_shm(name, size):
    try:
        shm = shared_memory.SharedMemory(name=name)
        arr = np.ndarray((size[1], size[0], 3), dtype=np.uint8, buffer=shm.buf)
        return shm, arr
    except Exception:
        return None, None


def ui_loop():
    root = tk.Tk()
    root.title("Autobotic UI")
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
    ttk.Button(mode_frame, text="Line", command=lambda: objective.__setattr__("value", "follow_line")).grid(row=0, column=0, padx=4, pady=2)
    ttk.Button(mode_frame, text="Zone", command=lambda: objective.__setattr__("value", "zone")).grid(row=0, column=1, padx=4, pady=2)
    ttk.Button(mode_frame, text="Manual", command=lambda: objective.__setattr__("value", "manual")).grid(row=0, column=2, padx=4, pady=2)

    calib_frame = ttk.LabelFrame(left, text="Calibration", padding=8)
    calib_frame.grid(row=7, column=0, sticky="ew", pady=(8, 0))
    ttk.Button(calib_frame, text="Line Green", command=lambda: (calibration_color.__setattr__("value", "l-gl"), calibrate_color_status.__setattr__("value", "calibrate"))).grid(row=0, column=0, padx=3, pady=2)
    ttk.Button(calib_frame, text="Line Black", command=lambda: (calibration_color.__setattr__("value", "l-bn"), calibrate_color_status.__setattr__("value", "calibrate"))).grid(row=0, column=1, padx=3, pady=2)
    ttk.Button(calib_frame, text="Line Red", command=lambda: (calibration_color.__setattr__("value", "l-rl"), calibrate_color_status.__setattr__("value", "calibrate"))).grid(row=0, column=2, padx=3, pady=2)
    ttk.Button(calib_frame, text="Zone Green", command=lambda: (calibration_color.__setattr__("value", "z-g"), calibrate_color_status.__setattr__("value", "calibrate"))).grid(row=1, column=0, padx=3, pady=2)
    ttk.Button(calib_frame, text="Zone Red", command=lambda: (calibration_color.__setattr__("value", "z-r"), calibrate_color_status.__setattr__("value", "calibrate"))).grid(row=1, column=1, padx=3, pady=2)
    ttk.Button(calib_frame, text="Check", command=lambda: calibrate_color_status.__setattr__("value", "check")).grid(row=1, column=2, padx=3, pady=2)

    action_frame = ttk.LabelFrame(left, text="Actions", padding=8)
    action_frame.grid(row=8, column=0, sticky="ew", pady=(8, 0))

    def toggle_light():
        light_on.value = not light_on.value

    ttk.Button(action_frame, text="Toggle Light", command=toggle_light).grid(row=0, column=0, padx=4, pady=2)

    def on_quit():
        terminate.value = True
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

    cam1_label = tk.Label(cam_frame, text="Line Camera", bg="#222", fg="#ccc")
    cam1_label.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
    cam2_label = tk.Label(cam_frame, text="Zone Camera", bg="#333", fg="#ccc")
    cam2_label.grid(row=1, column=0, padx=6, pady=6, sticky="nsew")

    cam1_img = None
    cam2_img = None

    shm_line, arr_line = attach_shm(LINE_SHM_NAME, LINE_SIZE)
    shm_zone, arr_zone = attach_shm(ZONE_SHM_NAME, ZONE_SIZE)

    def refresh():
        nonlocal cam1_img, cam2_img, shm_line, arr_line, shm_zone, arr_zone
        if terminate.value:
            on_quit()
            return

        labels["status"].set(status.value)
        labels["objective"].set(objective.value)
        labels["line"].set(f"{'found' if line_found.value else 'lost'} err={line_error_x.value:.2f}")
        labels["turn"].set(turn_direction.value)
        labels["exit"].set(f"{exit_angle.value:.1f}")
        labels["silver"].set(f"{silver_prob.value:.3f}")
        labels["imu"].set(f"yaw={imu_yaw.value:.1f} pitch={imu_pitch.value:.1f} roll={imu_roll.value:.1f}")
        labels["ir"].set(f"IR1={ir1.value} IR2={ir2.value} IRB={ir_back.value}")
        labels["ball"].set(f"{ball_type.value} err={ball_error_x.value:.2f} conf={ball_conf.value:.2f} w={ball_box_width.value:.0f}")
        labels["zone"].set(f"G:{zone_green_found.value} err={zone_green_error_x.value:.2f} | R:{zone_red_found.value} err={zone_red_error_x.value:.2f}")
        labels["victim"].set(f"Alive:{alive_count.value} Dead:{dead_count.value}")

        light_var.set("Light: ON" if light_on.value else "Light: OFF")
        light_label.configure(bg="#1b5e20" if light_on.value else "#444")

        try:
            if arr_line is None:
                shm_line, arr_line = attach_shm(LINE_SHM_NAME, LINE_SIZE)
            if arr_line is not None:
                img = Image.fromarray(arr_line.copy())
                img = img.resize((520, 292))
                cam1_img = ImageTk.PhotoImage(img)
                cam1_label.configure(image=cam1_img, text="")
        except Exception:
            pass

        try:
            if arr_zone is None:
                shm_zone, arr_zone = attach_shm(ZONE_SHM_NAME, ZONE_SIZE)
            if arr_zone is not None:
                img = Image.fromarray(arr_zone.copy())
                img = img.resize((520, 292))
                cam2_img = ImageTk.PhotoImage(img)
                cam2_label.configure(image=cam2_img, text="")
        except Exception:
            pass

        root.after(200, refresh)

    refresh()
    root.mainloop()

    if shm_line:
        try:
            shm_line.close()
        except Exception:
            pass
    if shm_zone:
        try:
            shm_zone.close()
        except Exception:
            pass
