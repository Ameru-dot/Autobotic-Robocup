# RoboCup Rescue Line: Lesson Plan 1-5 (tanpa robot)

Dokumen ini guna kandungan dalam repo ini sebagai rujukan. Semua lesson boleh diajar tanpa robot fizikal.

## Lesson 1: Pengenalan RoboCup Rescue Line (wajib tanpa robot)

Objektif
- Faham konsep RoboCup Junior Rescue Line dan misi robot.
- Kenal struktur pertandingan, elemen trek, dan cara scoring.
- Kenal dokumen wajib: rules, TDP, poster, engineering journal.

Kandungan utama
- Pengenalan liga Rescue Line: misi, objektif, dan contoh trek.
- Elemen trek: line hitam, gap, persimpangan hijau, halangan, ramp, dan evacuation zone.
- Scoring ringkas: kesilapan, bantuan manusia, dan penalti.
- Dokumen pertandingan: TDP, poster, engineering journal.

Aktiviti kelas (tanpa robot)
- Baca ringkasan peraturan dan tanda elemen trek pada lukisan A4.
- Main "scoring scenario": beri 2-3 situasi, pelajar kira markah ikut rules.
- Diskusi ringkas: kenapa robot perlu autonoma dan konsisten.

Tugasan ringkas
- Tulis 1 halaman ringkas: "Apa cabaran utama Rescue Line dan cara mengatasi."

Rujukan repo
- `documents/rules/RCJRescueLine2024-final.pdf`
- `documents/rules/Scoring_Explained_2024.pdf`
- `documents/documentation/Engineering Journal.pdf`
- `documents/documentation/Team Description Paper.pdf`
- `documents/documentation/Poster.pdf`

## Lesson 2: Sistem Robot Rescue Line (arsitektur keseluruhan)

Objektif
- Faham pipeline asas: sensing -> perception -> decision -> actuation.
- Faham komponen utama robot Rescue Line.
- Boleh lakar block diagram sistem.

Kandungan utama
- Sensor asas: kamera, IR, gyro, encoder (konsep).
- Pemprosesan imej vs AI.
- Kawalan motor dan aktuator (servo, motor driver).
- Komunikasi antara modul (contoh: serial Arduino).

Aktiviti kelas (tanpa robot)
- Lakar block diagram sistem robot berdasarkan poster atau README.
- Kecilkan kepada 5 blok utama dan terangkan data flow.

Tugasan ringkas
- Sediakan 1 slaid sistem robot (block diagram + 5 ayat).

Rujukan repo
- `README.md`
- `documents/documentation/Poster.pdf`
- `documents/documentation/Engineering Journal.pdf`

## Lesson 3: Struktur Perisian dalam Repo (bacaan kod)

Objektif
- Faham struktur folder `robot_v.3/Python/main`.
- Kenal peranan fail utama dan proses multiprocessing.
- Boleh jejak aliran data dari kamera ke kawalan motor.

Kandungan utama
- Struktur utama: `main.py`, `line_cam.py`, `zone_cam.py`, `control.py`, `mp_manager.py`.
- Konsep multiprocessing untuk baca sensor dan kamera serentak.
- Konfigurasi asas (`config.ini`).

Aktiviti kelas (tanpa robot)
- Buka kod dan bina flowchart ringkas (tanpa run).
- Tandakan input dan output setiap modul.

Tugasan ringkas
- Tulis ringkasan 8-10 baris: "Modul apa yang paling kritikal dan kenapa."

Rujukan repo
- `robot_v.3/Python/main/main.py`
- `robot_v.3/Python/main/line_cam.py`
- `robot_v.3/Python/main/zone_cam.py`
- `robot_v.3/Python/main/control.py`
- `robot_v.3/Python/main/mp_manager.py`
- `robot_v.3/Python/main/config.ini`

## Lesson 4: Asas Computer Vision untuk Line Tracking

Objektif
- Faham asas grayscale, thresholding, dan ROI.
- Faham konsep line detection dan intersection.
- Boleh kaitkan teori dengan modul `line_cam.py`.

Kandungan utama
- Preprocessing: resize, blur, threshold.
- ROI dan kenapa fokus pada kawasan tertentu.
- Idea asas untuk kesan line dan arah.

Aktiviti kelas (tanpa robot)
- Lakarkan proses pipeline CV di papan putih.
- Bandingkan 2 pendekatan: rule-based vs AI.

Tugasan ringkas
- Buat pseudo-code 15-20 baris untuk line tracking ringkas.

Rujukan repo
- `robot_v.3/Python/main/line_cam.py`
- `robot_v.3/Python/test/color_calibration.py`
- `robot_v.3/Python/test/get_silver_angle.py`

## Lesson 5: AI, Dataset, dan Dokumentasi Pertandingan

Objektif
- Faham kenapa AI digunakan dalam Rescue Line (victim dan silver strip).
- Faham asas dataset dan model inference.
- Faham keperluan dokumentasi pertandingan.

Kandungan utama
- Ringkas AI pipeline: dataset -> training -> export -> inference.
- Model yang digunakan: YOLO (victim), classify (silver strip).
- Pentingnya engineering journal, TDP, dan poster.

Aktiviti kelas (tanpa robot)
- Bincang contoh dataset dan kriteria gambar yang baik.
- Outline 1 halaman TDP (tajuk dan isi penting).

Tugasan ringkas
- Draf struktur TDP: objektif, hardware, software, ujian, result.

Rujukan repo
- `README.md`
- `robot_v.3/Ai/datasets/images_to_annotate/annotator.py`
- `robot_v.3/Ai/models/ball_zone_s/ball_detect_s_edgetpu.tflite`
- `robot_v.3/Ai/models/silver_zone_entry/silver_classify_s.onnx`
- `documents/documentation/Engineering Journal.pdf`
- `documents/documentation/Team Description Paper.pdf`
- `documents/documentation/Poster.pdf`