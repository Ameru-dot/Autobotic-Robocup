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

# Shared memory names and sizes (must match line_cam/zone_cam)
LINE_SHM_NAME = "shm_line"
ZONE_SHM_NAME = "shm_zone"
LINE_SIZE = (448, 252)   # width, height
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
    root.title("Mine UI (tkinter)")
    root.geometry("960x620")
    root.resizable(False, False)

    labels = {
        "status": tk.StringVar(),
        "objective": tk.StringVar(),
        "line": tk.StringVar(),
        "exit_ang": tk.StringVar(),
        "silver": tk.StringVar(),
        "imu": tk.StringVar(),
        "ir": tk.StringVar(),
        "ball": tk.StringVar(),
        "turn_dir": tk.StringVar(),
        "zone": tk.StringVar(),
        "victim": tk.StringVar(),
    }

    ttk.Label(root, text="Status").grid(row=0, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["status"]).grid(row=0, column=1, sticky="w")

    ttk.Label(root, text="Objective").grid(row=1, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["objective"]).grid(row=1, column=1, sticky="w")

    ttk.Label(root, text="Line").grid(row=2, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["line"]).grid(row=2, column=1, sticky="w")

    ttk.Label(root, text="Turn").grid(row=3, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["turn_dir"]).grid(row=3, column=1, sticky="w")

    ttk.Label(root, text="Exit Ang").grid(row=4, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["exit_ang"]).grid(row=4, column=1, sticky="w")

    ttk.Label(root, text="Silver").grid(row=5, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["silver"]).grid(row=5, column=1, sticky="w")

    ttk.Label(root, text="IMU").grid(row=6, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["imu"]).grid(row=6, column=1, sticky="w")

    ttk.Label(root, text="IR").grid(row=7, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["ir"]).grid(row=7, column=1, sticky="w")

    ttk.Label(root, text="Ball").grid(row=8, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["ball"]).grid(row=8, column=1, sticky="w")

    ttk.Label(root, text="Zone").grid(row=9, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["zone"]).grid(row=9, column=1, sticky="w")

    ttk.Label(root, text="Victims").grid(row=10, column=0, sticky="w", padx=6, pady=4)
    ttk.Label(root, textvariable=labels["victim"]).grid(row=10, column=1, sticky="w")

    # Mode buttons
    btn_frame = ttk.Frame(root)
    btn_frame.grid(row=11, column=0, columnspan=2, pady=8)
    ttk.Button(btn_frame, text="Mode: Line", command=lambda: objective.__setattr__("value", "follow_line")).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="Mode: Zone", command=lambda: objective.__setattr__("value", "zone")).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="Mode: Manual", command=lambda: objective.__setattr__("value", "manual")).pack(side="left", padx=4)

    # Calibration buttons
    calib_frame = ttk.Frame(root)
    calib_frame.grid(row=12, column=0, columnspan=2, pady=8)
    ttk.Button(calib_frame, text="Calib Line Green", command=lambda: (calibration_color.__setattr__("value", "l-gl"), calibrate_color_status.__setattr__("value", "calibrate"))).pack(side="left", padx=4)
    ttk.Button(calib_frame, text="Calib Line Black", command=lambda: (calibration_color.__setattr__("value", "l-bn"), calibrate_color_status.__setattr__("value", "calibrate"))).pack(side="left", padx=4)
    ttk.Button(calib_frame, text="Calib Line Red", command=lambda: (calibration_color.__setattr__("value", "l-rl"), calibrate_color_status.__setattr__("value", "calibrate"))).pack(side="left", padx=4)
    ttk.Button(calib_frame, text="Calib Zone Green", command=lambda: (calibration_color.__setattr__("value", "z-g"), calibrate_color_status.__setattr__("value", "calibrate"))).pack(side="left", padx=4)
    ttk.Button(calib_frame, text="Calib Zone Red", command=lambda: (calibration_color.__setattr__("value", "z-r"), calibrate_color_status.__setattr__("value", "calibrate"))).pack(side="left", padx=4)
    ttk.Button(calib_frame, text="Check", command=lambda: calibrate_color_status.__setattr__("value", "check")).pack(side="left", padx=4)

    # Light toggle
    def toggle_light():
        light_on.value = not light_on.value
    light_btn = ttk.Button(root, text="Toggle Light", command=toggle_light)
    light_btn.grid(row=13, column=0, columnspan=2, pady=6)

    # Camera placeholders
    cam_frame = ttk.Frame(root, borderwidth=1, relief="groove")
    cam_frame.grid(row=0, column=2, rowspan=17, padx=8, pady=8, sticky="nsew")
    cam_frame.grid_columnconfigure(0, weight=1)
    cam_frame.grid_rowconfigure(0, weight=1)
    cam_frame.grid_rowconfigure(1, weight=1)

    cam1_label = tk.Label(cam_frame, text="Camera 1\n(Line)", bg="#222", fg="#ccc", width=48, height=12)
    cam1_label.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")
    cam2_label = tk.Label(cam_frame, text="Camera 2\n(Zone)", bg="#333", fg="#ccc", width=48, height=12)
    cam2_label.grid(row=1, column=0, padx=4, pady=4, sticky="nsew")

    cam1_img = None
    cam2_img = None

    shm_line, arr_line = attach_shm(LINE_SHM_NAME, LINE_SIZE)
    shm_zone, arr_zone = attach_shm(ZONE_SHM_NAME, ZONE_SIZE)

    def refresh():
        nonlocal cam1_img, cam2_img, shm_line, arr_line, shm_zone, arr_zone
        if terminate.value:
            try:
                root.destroy()
            except Exception:
                pass
            return

        labels["status"].set(status.value)
        labels["objective"].set(objective.value)
        labels["line"].set(f"{'found' if line_found.value else 'lost'} err={line_error_x.value:.2f}")
        labels["turn_dir"].set(turn_direction.value)
        labels["exit_ang"].set(f"{exit_angle.value:.1f}")
        labels["silver"].set(f"{silver_prob.value:.3f}")
        labels["imu"].set(f"yaw={imu_yaw.value:.1f} pitch={imu_pitch.value:.1f} roll={imu_roll.value:.1f}")
        labels["ir"].set(f"IR1={ir1.value} IR2={ir2.value} IRB={ir_back.value}")
        labels["ball"].set(f"{ball_type.value} err={ball_error_x.value:.2f} conf={ball_conf.value:.2f} w={ball_box_width.value:.0f}")
        labels["zone"].set(f"G:{zone_green_found.value} err={zone_green_error_x.value:.2f} | R:{zone_red_found.value} err={zone_red_error_x.value:.2f}")
        labels["victim"].set(f"Alive:{alive_count.value} Dead:{dead_count.value}")

        # Try to refresh camera frames
        try:
            if arr_line is None:
                shm_line, arr_line = attach_shm(LINE_SHM_NAME, LINE_SIZE)
            if arr_line is not None:
                img = Image.fromarray(arr_line.copy())
                img = img.resize((480, 270))
                cam1_img = ImageTk.PhotoImage(img)
                cam1_label.configure(image=cam1_img, text="")
        except Exception:
            pass

        try:
            if arr_zone is None:
                shm_zone, arr_zone = attach_shm(ZONE_SHM_NAME, ZONE_SIZE)
            if arr_zone is not None:
                img = Image.fromarray(arr_zone.copy())
                img = img.resize((480, 270))
                cam2_img = ImageTk.PhotoImage(img)
                cam2_label.configure(image=cam2_img, text="")
        except Exception:
            pass

        root.after(200, refresh)

    def on_quit():
        terminate.value = True
        try:
            root.destroy()
        except Exception:
            pass
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

    quit_btn = ttk.Button(root, text="Quit", command=on_quit)
    quit_btn.grid(row=15, column=0, columnspan=2, pady=12)

    refresh()
    root.mainloop()
