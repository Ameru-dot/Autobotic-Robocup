# Mine Setup Guide (RDK X5 + Arduino + Omni + Dual Camera)

## Hardware Summary
- Compute: RDK X5
- Motor driver: L298N (4 omni wheels, pins on Arduino)
- Arduino: Mega (recommended for pin count), serial 115200
- IMU: MPU-6050 (I2C on Arduino)
- IR sensors: front IR1=A2, IR2=A3, optional back IRB=A4 (Arduino)
- Servos: 6 (G1/K1/K2/S1/S2/C1) on Arduino pins 24-29 (adjust to your hardware)
- Cameras: Raspberry Pi Camera V2 x2 via 22-to-15 adapter (Line cam index=1, Zone cam index=0)
- Light/LED: Arduino LED_PIN=22 (relay/LED control)
- Power: Buck 12V->5V 5A+ for board; motors from 12V; common ground; LED/servos on proper 5-6V rail (not from board 5V)

## Arduino Firmware
- Sketch: `robot_v.3/Python/mine/arduino_bridge.ino`
- Serial commands:
  - `M <fl> <fr> <bl> <br>`  (motor -255..255)
  - `STOP`, `PING`, `LED <0|1>`
  - `SVP <id>` servo presets (1 lower_arm, 2 raise_arm_left, 3 raise_arm_right, 4 open gate1, 5 close gate1, 6 open gate2, 7 close gate2)
- Telemetry every 50 ms: `IMU X:.. Y:.. Z:..`, `IR1 ..`, `IR2 ..`, `IRB ..`
- Update pin mapping if needed (motors, IR, servos, LED)

## Board Software (folder `robot_v.3/Python/mine`)
Key processes:
- `main.py`: launcher (line_cam, zone_cam, serial, control, ui, manual_control)
- `line_cam.py`: line detect, marker hijau, garis merah (exit) + overlay; writes to `shm_line`; calibration to `config_mine.ini`
- `zone_cam.py`: ball detect (YOLO .pt/NCNN), zone color offsets (green/red), ball box width, writes to `shm_zone`
- `control.py`: state machine:
  - follow_line with speed scaling, gap mode, exit red stop (angle)
  - zone: strafe approach to ball, pick (servo presets), go_drop (align to green/red), turn+reverse dump (IRB/timer), exit when done
  - manual: WASD/QE via pygame (manual_control.py)
  - light auto (on line/zone), calibration freeze
- `sensor_serial.py`: parse IMU/IR/IRB, send motor/LED/SVP commands
- `ui_tk.py`: UI with mode buttons, calibration buttons, light toggle, camera feeds, status/IR/IMU/ball/zone/victim counts/exit angle
- `config_mine.ini`: HSV/threshold defaults (line/zone); calibration writes here

Dependencies (RDK X5):
- python packages: opencv-python, numpy, pillow, ultralytics (for YOLO), pygame (manual control)
- optional: NCNN runtime / vendor NPU SDK if you want NPU inference
- tkinter is standard; ensure PIL/Pillow installed

## NPU (NCNN) optional
- Export example (Ultralytics): `YOLO("ball_detect_s.pt").export(format="ncnn")`
- Put the exported NCNN model folder under `robot_v.3/Ai/models/ball_zone_s/`
- Update `robot_v.3/Python/mine/zone_cam.py` `MODEL_PATH` to the NCNN folder

## Running
1) Flash Arduino with `arduino_bridge.ino` (confirm pins, IMU, IRB). Connect via USB (/dev/ttyUSB0 default).
2) Set camera indices (line_cam CAM_INDEX=1, zone_cam CAM_INDEX=0), serial port in sensor_serial.py. Verify `/dev/video*` exists on RDK.
3) Ensure `config_mine.ini` writable; adjust HSV if needed.
4) Run: `python robot_v.3/Python/mine/main.py`
5) UI appears; use mode buttons (Line/Zone/Manual), calibration buttons (Line/Zone colors), light toggle. Quit to stop (sends STOP).

### Step-by-step quick start
- Wiring: connect cameras to RDK; Arduino to USB; motors to L298N (pins per arduino_bridge.ino); IR front to A2/A3, IR back to A4; servo to pins 24-29; LED/relay to pin 22.
- Power: board from 5V 5A buck (common ground), motors from 12V; separate servo 5-6V supply recommended.
- Flash Arduino: open `arduino_bridge.ino`, set pins if needed, upload to Mega.
- Board deps: install opencv-python, numpy, pillow, ultralytics, pygame. Ensure Tkinter available.
- Check config: `config_mine.ini` has HSV defaults; editable via calibration buttons.
- Run: `python robot_v.3/Python/mine/main.py`
- UI: pick mode (Line/Zone/Manual), run calibration as needed (Line/Zone colors), toggle light if needed.
- Observe feeds/labels: line error, turn dir, exit angle, IR/IRB, ball info, zone offsets, victim counts.
- Stop: use Quit button or Ctrl+C (sends STOP to Arduino).

## Notes / Tuning
- Speed scaling: `TURN_SPEED_GAIN`, `MIN_SPEED_SCALE` in control.py
- Gap mode: `GAP_LOST_TIME`, `GAP_MAX_TIME`, `GAP_SPEED`
- Zone approach: `KX_BALL`, `BALL_ALIGN_ERR`, `BALL_WIDTH_THRESH`, `VY_APPROACH`
- Drop: IR thresholds `IR_FRONT_DROP`, `IR_BACK_DROP`, timers `TURN180_TIME`, `BACK_TIME`
- Exit: stop on red if `|exit_angle| < EXIT_ANGLE_TOL`
- Light auto: `LIGHT_AUTO` in control.py
- Servo presets may need adjustment for your mechanics

## Limitations (current)
- No full ramp/gap/obstacle logic from original main; IR used mainly as block/dump distance
- Zone pickup/dump heuristic (width-based distance, timer turn/back); no precise range sensing
- No gripper feedback; preset-based
- NPU/NCNN is optional; default uses `.pt` CPU. If you export to NCNN, update MODEL_PATH and install the runtime.

