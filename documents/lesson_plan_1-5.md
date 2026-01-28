# RoboCup Rescue Line: Lesson Plan 1-12 (Autobotic_v3)

Dokumen ini guna kod dalam `robot_v.3/Python/Autobotic_v3` sebagai rujukan utama.
Fokus pada aliran sebenar sistem (kamera, line, zone, kawalan, motor, sensor) dan latihan berperingkat.

## Lesson 1: Orientation & Team Roles

Objective
- To introduce the training program, clarify team roles, and establish awareness of RoboCup rules and documentation requirements.

Learning outcomes
- Pelajar boleh senaraikan peranan: software, hardware, dokumentasi, testing.
- Pelajar faham ringkas rules Rescue Line (green marker, intersection, silver, zone).
- Pelajar tahu dokumen wajib: TDP, poster, engineering journal.

Aktiviti
- Agihkan peranan pasukan dan senarai tugasan mingguan.
- Quiz ringkas rules + contoh situasi scoring.

Rujukan repo
- `documents/rules/RCJRescueLine2024-final.pdf`
- `documents/documentation/Engineering Journal.pdf`
- `documents/documentation/Team Description Paper.pdf`
- `documents/documentation/Poster.pdf`

## Lesson 2: Software Architecture

Objective
- To understand how the existing robot software system operates and how processes communicate with each other.

Learning outcomes
- Pelajar boleh terangkan peranan setiap proses dalam `main.py`.
- Pelajar faham `mp_manager.py` sebagai shared memory.
- Pelajar boleh lukis flow data dari kamera ke motor.

Aktiviti
- Bina flowchart proses: `line_cam`, `zone_cam`, `control`, `motor_serial`, `sensor_serial`.

Rujukan repo
- `robot_v.3/Python/Autobotic_v3/main.py`
- `robot_v.3/Python/Autobotic_v3/mp_manager.py`
- `robot_v.3/Python/Autobotic_v3/main_test.py`

## Lesson 3: Line & Marker Optimization

Objective
- To optimize line following and marker-based decision making for stable and accurate navigation.

Learning outcomes
- Pelajar faham pipeline CV line/marker dalam `line_cam.py`.
- Pelajar boleh ubah threshold warna dari `config.ini`.
- Pelajar boleh interpret `turn_direction` dan `line_error_x`.

Aktiviti
- Run `line_detect_test.py` dan perhatikan mask/line angle.
- Tuning nilai `black_max_*`, `green_min/max` dalam `config.ini`.

Rujukan repo
- `robot_v.3/Python/Autobotic_v3/line_cam.py`
- `robot_v.3/Python/Autobotic_v3/config.ini`
- `robot_v.3/Python/Autobotic_v3/line_detect_test.py`

## Lesson 4: Motor Performance Tuning

Objective
- To refine motor control for smooth, responsive, and precise robot movement.

Learning outcomes
- Pelajar tahu mapping motor M1-M4 dan arah roda.
- Pelajar boleh ubah gain motor di `control.py`.
- Pelajar boleh uji manual drive tanpa line.

Aktiviti
- Uji `manual_control.py` untuk respon omni.
- Laras `KP_TURN`, `VY_CMD`, `TURN_SPEED_GAIN`.

Rujukan repo
- `robot_v.3/Python/Autobotic_v3/motor_serial.py`
- `robot_v.3/Python/Autobotic_v3/motor_driver.py`
- `robot_v.3/Python/Autobotic_v3/control.py`
- `robot_v.3/Python/Autobotic_v3/manual_control.py`

## Lesson 5: Sensor Verification

Objective
- To validate sensor reliability and ensure accurate communication between hardware and software.

Learning outcomes
- Pelajar boleh baca data IMU/IR dari Arduino.
- Pelajar boleh sahkan port serial betul (Arduino vs motor).
- Pelajar boleh debug isu sensor secara sistematik.

Aktiviti
- Test bacaan IMU/IR di log.
- Semak peranan Arduino hanya untuk sensor/servo.

Rujukan repo
- `robot_v.3/Python/Autobotic_v3/sensor_serial.py`
- `robot_v.3/Python/Autobotic_v3/arduino_bridge.ino`

## Lesson 6: Control Stability

Objective
- To achieve consistent and stable turning behavior using IMU-based yaw control.

Learning outcomes
- Pelajar faham logik turn 90/180 menggunakan IMU.
- Pelajar boleh laras `TURN_*` parameter.
- Pelajar boleh nilai kestabilan turn di persimpangan.

Aktiviti
- Uji turn kiri/kanan menggunakan marker hijau.
- Bandingkan hasil sebelum/selepas tuning.

Rujukan repo
- `robot_v.3/Python/Autobotic_v3/control.py`
- `robot_v.3/Python/Autobotic_v3/mp_manager.py`

## Lesson 7: Mechanical Reliability

Objective
- To ensure mechanical alignment and stability for consistent robot performance during runs.

Learning outcomes
- Pelajar boleh set wheel alignment dan ketegangan mekanikal.
- Pelajar boleh kesan isu getaran dan drift.
- Pelajar boleh buat checklist mekanikal sebelum run.

Aktiviti
- Pemeriksaan chassis, wheel, dan bracket kamera.
- Test drag/geseran pada roda omni.

Rujukan repo
- `documents/mine_setup.md`

## Lesson 8: Camera & Vision Stability

Objective
- To improve vision accuracy by optimizing camera placement and minimizing vibration effects.

Learning outcomes
- Pelajar boleh pilih sudut kamera line/zone yang stabil.
- Pelajar faham kesan crop dan resolusi pada FPS.
- Pelajar boleh uji kamera secara berasingan.

Aktiviti
- Run `test_line.py` dan `zone_test.py`.
- Laras `LINE_CAM_DEVICE` dan `ZONE_CAM_DEVICE`.

Rujukan repo
- `robot_v.3/Python/Autobotic_v3/test_line.py`
- `robot_v.3/Python/Autobotic_v3/zone_test.py`
- `robot_v.3/Python/Autobotic_v3/line_cam.py`
- `robot_v.3/Python/Autobotic_v3/zone_cam.py`

## Lesson 9: Power & Electrical Safety

Objective
- To ensure electrical stability, safe wiring practices, and prevent power-related failures.

Learning outcomes
- Pelajar tahu pemisahan kuasa motor vs logic.
- Pelajar boleh kenal simptom brownout.
- Pelajar boleh susun wiring yang selamat.

Aktiviti
- Audit wiring, fuse, dan connector.
- Uji voltage drop semasa motor full load.

Rujukan repo
- `documents/mine_setup.md`

## Lesson 10: Zone & Ball Execution

Objective
- To optimize ball detection, pickup, and drop performance during zone tasks.

Learning outcomes
- Pelajar faham pipeline detection bola dan corner drop.
- Pelajar boleh interpret `ball_error_x`, `ball_conf`.
- Pelajar boleh tune logik zone dalam `control.py`.

Aktiviti
- Uji detection dengan `zone_cam.py` + mock ball.
- Simulasi deposit green/red.

Rujukan repo
- `robot_v.3/Python/Autobotic_v3/zone_cam.py`
- `robot_v.3/Python/Autobotic_v3/control.py`
- `robot_v.3/Ai/models/ball_zone_s/ball_detect_s_edgetpu.tflite`

## Lesson 11: Full Run & Troubleshooting

Objective
- To identify, diagnose, and resolve system-level issues through full-course testing.

Learning outcomes
- Pelajar boleh jalankan `main.py` dan baca status.
- Pelajar boleh diagnose isu kamera/motor/sensor.
- Pelajar boleh buat log ringkas setiap run.

Aktiviti
- Full run di trek, catat isu.
- Bandingkan hasil `main_test.py` vs `main.py`.

Rujukan repo
- `robot_v.3/Python/Autobotic_v3/main.py`
- `robot_v.3/Python/Autobotic_v3/main_test.py`
- `robot_v.3/Python/Autobotic_v3/ui_tk.py`

## Lesson 12: Competition Simulation

Objective
- To prepare students for real RoboCup competition conditions, including timing, rules, and final documentation.

Learning outcomes
- Pelajar boleh simulasi run ikut rules dan timing.
- Pelajar boleh siapkan dokumentasi lengkap.
- Pelajar boleh buat checklist final sebelum pertandingan.

Aktiviti
- Simulasi penuh 1 run + scoring.
- Semak TDP/Poster/Journal akhir.

Rujukan repo
- `documents/documentation/Engineering Journal.pdf`
- `documents/documentation/Team Description Paper.pdf`
- `documents/documentation/Poster.pdf`
