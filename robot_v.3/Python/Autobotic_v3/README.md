# Autobotic_v3

This folder contains the multi-process control stack for the RoboCup Rescue Line robot.
It is configured for:
- RDK X5 (Linux)
- Dual USB webcams via OpenCV (line + zone)
- Yahboom 4-channel motor driver over USB serial
- Arduino Mega for IMU/IR sensors + servos (no motor control)

Use this README as the main setup + run guide for the Autobotic_v3 code.

## System overview

Data flow (high level):
1) `line_cam.py` reads the down-facing camera, detects line/markers, and writes shared values.
2) `zone_cam.py` reads the front camera, detects balls/corners, and writes shared values.
3) `control.py` reads shared values and decides movement.
4) `motor_serial.py` sends motor targets to Yahboom driver.
5) `sensor_serial.py` reads IMU/IR from Arduino and drives servos/LED.
6) `ui_tk.py` provides UI + calibration tools.

Processes are launched from `main.py` using multiprocessing and shared state in `mp_manager.py`.

## Key entry points

- `main.py` ? full system (camera + control + motor + sensor + UI)
- `main_test.py` ? camera + control only (no motor/Arduino)
- `line_detect_test.py` ? line detection only (no motor)
- `test_line.py` ? raw line camera preview
- `zone_test.py` ? raw zone camera preview

## Folder map (core files)

- `main.py` ? launches all processes
- `main_test.py` ? safe run without hardware
- `mp_manager.py` ? shared state (multiprocessing Manager)
- `line_cam.py` ? line + green marker detection
- `zone_cam.py` ? ball + zone detection
- `control.py` ? decision logic and movement control
- `motor_serial.py` ? Yahboom motor commands
- `motor_driver.py` ? Yahboom motor driver API wrapper
- `sensor_serial.py` ? Arduino serial IO (IMU/IR/servo)
- `manual_control.py` ? manual driving via keyboard (pygame)
- `ui_tk.py` ? GUI + calibration

## Hardware mapping

Serial ports (default):
- Motor driver (Yahboom): `/dev/ttyUSB0`
- Arduino Mega: `/dev/ttyACM0`

Cameras (default):
- Line camera (down): `/dev/video0`
- Zone camera (front): `/dev/video2`

You can override camera devices using environment variables:
```bash
LINE_CAM_DEVICE=/dev/video0
ZONE_CAM_DEVICE=/dev/video2
```


## Wiring (summary)

- Power: motor driver from motor battery, compute board + Arduino from regulated 5V (or USB).
- Ground: share common ground between motor driver, Arduino, and RDK.
- USB: RDK -> Yahboom motor driver (`/dev/ttyUSB0`), RDK -> Arduino Mega (`/dev/ttyACM0`).
- Motors: M1/M2 left, M3/M4 right (adjust `MOTOR_ORDER`/`MOTOR_INVERT` if wiring differs).
- Servos: use a separate 5V regulator if servo current is high; do not overload Arduino 5V.
- Cameras: USB webcams to RDK; confirm device IDs with `ls /dev/video*`.
- Safety: add a main power switch and fuse on the motor battery line.

## Camera test quickstart

Line camera raw preview:
```bash
LINE_CAM_DEVICE=/dev/video0 python3 test_line.py
```

Zone camera raw preview:
```bash
ZONE_CAM_DEVICE=/dev/video2 python3 zone_test.py
```

Line detection test (no motor):
```bash
LINE_CAM_DEVICE=/dev/video0 python3 line_detect_test.py
```

Press `q` to quit test windows.

## Software setup (RDK X5)

Recommended: create a virtual environment in this folder.
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python packages:
```bash
pip install opencv-python numpy ultralytics scikit-image numba pillow python-prctl onnx onnxruntime
```

If `python-prctl` fails to build, install system headers first:
```bash
sudo apt-get update
sudo apt-get install -y libcap-dev
```

Note: on ARM, `onnxruntime` may take time to install.

## Run commands

Full system (requires motor + Arduino connected):
```bash
cd ~/Autobotic-Robocup/robot_v.3/Python/Autobotic_v3
LINE_CAM_DEVICE=/dev/video0 ZONE_CAM_DEVICE=/dev/video2 python3 main.py
```

Safe run without hardware:
```bash
LINE_CAM_DEVICE=/dev/video0 ZONE_CAM_DEVICE=/dev/video2 python3 main_test.py
```

Headless mode (no display):
```bash
START_UI=0 python3 main_test.py
```

## UI and calibration

`ui_tk.py` provides live view, calibration, and status.
Calibration codes:
- Line: `l-gl`, `l-rl`, `l-bn`, `l-bd`, `l-bv`, `l-bvl`, `l-bz`, `l-gz`, `l-rz`
- Zone: `z-g`, `z-r`

Calibration writes values into `config.ini`.

## Configuration files

- `config.ini` ? main configuration (colors, thresholds, tuning)
- `config_mine.ini` ? local overrides (copy values into `config.ini` if needed)

## Control tuning (quick map)

Key parameters in `control.py`:
- Line following: `KP_TURN`, `VY_CMD`, `TURN_SPEED_GAIN`
- Turn logic: `TURN_*`, `TURN_USE_IMU`, `TURN_ANGLE_DEG`, `TURN_IMU_TOL`
- Zone: `KP_BALL`, `BALL_CONF_MIN`, `BALL_WIDTH_THRESH`
- Ramp: `RAMP_UP_PITCH`, `RAMP_DOWN_PITCH`

Key outputs from perception:
- Line: `line_error_x`, `line_found`, `turn_direction`
- Zone: `ball_error_x`, `ball_conf`, `zone_green_found`, `zone_red_found`

## Motor mapping

Default motor order (logical):
- M1 = left
- M2 = left
- M3 = right
- M4 = right

If wiring differs, adjust these in `motor_serial.py`:
- `MOTOR_ORDER`
- `MOTOR_INVERT`

## Arduino (sensor-only)

`arduino_bridge.ino` handles:
- IMU yaw/pitch/roll
- IR sensors
- Servo presets and LEDs

No motor control in Arduino.


## Arduino wiring (IMU + sensors + servos)

IMU (MPU-6050 over I2C):
- SDA -> Mega pin 20
- SCL -> Mega pin 21
- VCC -> 5V (or 3.3V depending on your MPU board)
- GND -> GND

Analog IR sensors:
- IR1 -> A2
- IR2 -> A3
- IR_BACK (optional) -> A4

LED/Relay:
- LED_PIN -> D22

Servo pins:
- G1 (Lift Arm) -> D24
- K1 (Rotate Gripper) -> D25
- K2 (Open/Close Gripper) -> D26
- S1 (Main Barrier) -> D27
- S2 (Dead Barrier) -> D28
- C1 (Camera) -> D29

Note: If your wiring differs, update pin mapping in `arduino_bridge.ino`.

## Git LFS (large weights)

`yolov3.weights` is large. Use Git LFS if you need to sync it:
```bash
git lfs install
git lfs track "*.weights"
git add .gitattributes yolov3.weights
git commit -m "Track YOLO weights"
git push
```

On RDK:
```bash
sudo apt-get install -y git-lfs
git lfs install
git lfs pull
```

## Troubleshooting

No camera window:
- Make sure you are in a GUI session (VNC/monitor), not pure SSH.
- Try running `test_line.py` or `zone_test.py` first.

Camera not found:
- Check `ls /dev/video*` and update `LINE_CAM_DEVICE` / `ZONE_CAM_DEVICE`.
- Swap device IDs if the cameras are reversed.

Serial permission error:
- Add user to dialout group: `sudo usermod -aG dialout $USER`
- Log out and back in.

`onnxruntime` install fails:
- Use system pip in venv, and ensure `python3.10` matches your wheel.

UI does not open:
- Set `START_UI=0` for headless or run VNC for GUI.

## Recommended test order

1) `test_line.py` and `zone_test.py` to confirm cameras.
2) `line_detect_test.py` to validate detection.
3) `main_test.py` to validate control logic without motors.
4) `main.py` on full hardware.
