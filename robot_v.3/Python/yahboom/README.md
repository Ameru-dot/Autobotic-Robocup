# Yahboom (Autobotic Logic + Yahboom Motor Driver)

Folder ini telah diselaraskan supaya **logic sama seperti `Autobotic_v3`**, tetapi **motor masih guna Yahboom motor driver**. Kamera menggunakan **CSI**:
- **Line camera**: Raspberry Pi Camera v1 (CSI)  
- **Zone camera**: Arducam (CSI)

---

## 1) Wiring (Ringkas & Tepat)

### A) RDK X5 ? Yahboom Motor Driver
- Sambung **USB** Yahboom driver ke RDK X5
- Port biasanya: `/dev/ttyUSB0`

### B) RDK X5 ? Arduino Mega (sensor/servo)
- Sambung **USB** Arduino Mega ke RDK X5
- Port biasanya: `/dev/ttyACM0`

### C) IMU MPU6050 ? Arduino Mega (I2C)
- VCC ? 5V
- GND ? GND
- SDA ? **Pin 20**
- SCL ? **Pin 21**

### D) IR Sensors ? Arduino Mega (Analog)
- IR1 ? **A2**
- IR2 ? **A3**
- IRB (belakang) ? **A4**
- VCC ? 5V
- GND ? GND

### E) LED Indicator (Optional)
- LED ? **D22** (guna resistor 220–330O)
- GND ? GND

### F) Servo (Jika ada, optional)
- Signal servo ? **D24–D29** (ikut code)
- VCC ? 5V (power berasingan jika banyak servo)
- GND ? GND

### G) CSI Cameras ? RDK X5
- **Line cam**: CSI0 (LINE_CAM_INDEX=0)
- **Zone cam**: CSI1 (ZONE_CAM_INDEX=1)

---

## 2) Port Mapping (Pentings)

### Motor Yahboom
- `robot_v.3/Python/yahboom/motor_serial.py`
- Default: `/dev/ttyUSB0` (ubah jika port lain)

### Arduino Mega
- `robot_v.3/Python/yahboom/sensor_serial.py`
- Default: `/dev/ttyACM0`

---

## 3) Setup Software (RDK)

### A) Clone & masuk folder
```bash
cd ~
git clone https://github.com/Ameru-dot/Autobotic-Robocup.git
cd ~/Autobotic-Robocup/robot_v.3/Python/yahboom
```

### B) Buat virtual env
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### C) Install dependencies
```bash
pip install -U pip setuptools wheel
pip install opencv-python numpy numba scikit-image ultralytics pillow pyserial
pip install picamera2
```

> Jika guna **ONNX** (silver detect), install:
```bash
pip install onnx onnxruntime
```

---

## 4) Cara Run

### A) Full system (line + zone + motor + UI)
```bash
LINE_CAM_INDEX=0 ZONE_CAM_INDEX=1 python3 main.py
```

### B) Line camera sahaja
```bash
LINE_CAM_INDEX=0 python3 test_line.py
```

### C) Zone camera sahaja
```bash
ZONE_CAM_INDEX=1 python3 zone_test.py
```

### D) Line + motor sahaja
```bash
LINE_CAM_INDEX=0 python3 main_line_motor.py
```

---

## 5) Catatan Penting

- **Jika port berubah**, semak:
```bash
ls /dev/ttyUSB*
ls /dev/ttyACM*
```
- **Jika kamera tidak keluar**, pastikan CSI terpasang betul dan guna index yang betul:
```bash
LINE_CAM_INDEX=0 ZONE_CAM_INDEX=1 python3 main.py
```
- **Motor mapping Yahboom** (dalam `motor_serial.py`):
  - M1 = kiri
  - M2 = kiri
  - M3 = kanan
  - M4 = kanan

---

## 6) Fail Utama

- `main.py` — full system
- `line_cam.py` — line detection
- `zone_cam.py` — zone & ball detection
- `control.py` — control logic (omni kinematics)
- `motor_serial.py` — Yahboom motor driver
- `sensor_serial.py` — Arduino IMU/IR/servo
- `ui_tk.py` — UI utama

---

## 7) Quick Troubleshoot

### Motor tak gerak
- Pastikan Yahboom driver detect `/dev/ttyUSB0`
- Pastikan power motor driver cukup

### Sensor tak masuk
- Pastikan Arduino detect `/dev/ttyACM0`
- Pastikan wiring SDA/SCL betul

### Camera tak keluar
- Pastikan CSI cable betul dan kamera dikenali
- Cuba test `test_line.py` / `zone_test.py`

---

Jika awak mahu saya tambah **diagram wiring** atau gambar, beritahu saja.
---

## 8) VNC (Remote Desktop)

### Cara cepat (GNOME Remote Desktop)
1. Di RDK: **Settings ? Sharing**
2. On **Remote Desktop / Screen Sharing**
3. Set **password**
4. Dari laptop (VNC Viewer) sambung ke:
```
<IP_RDK>:5900
```
Contoh:
```
192.168.0.29:5900
```

### Cara manual (x11vnc)
```bash
sudo apt update
sudo apt install -y x11vnc
x11vnc -storepasswd
x11vnc -forever -shared -display :0
```
Kemudian sambung VNC ke:
```
<IP_RDK>:5900
```
