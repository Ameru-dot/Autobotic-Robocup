import libsrcampy
import time

# Cipta objek kamera
cam = libsrcampy.Camera()

# Buka kamera MIPI
# Format: open_cam(pipe_id, video_index, fps, width, height)
ret = cam.open_cam(0, -1, 30, 1920, 1080)

if ret == 0:
    print("Kamera berjaya dibuka!")
    time.sleep(1)  # Tunggu ISP tuning selesai

    # Ambil satu bingkai imej
    img = cam.get_img(2)  # Modul 2 = output kamera
    if img is not None:
        with open("output.img", "wb") as f:
            f.write(img)
        print("Imej berjaya disimpan!")
    else:
        print("Gagal mendapatkan imej.")

    # Tutup kamera
    cam.close_cam()
else:
    print("Gagal membuka kamera. Kod ralat:", ret)
