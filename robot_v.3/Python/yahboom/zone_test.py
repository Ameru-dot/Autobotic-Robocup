import os
import time

import cv2

try:
    from picamera2 import Picamera2
except Exception:
    Picamera2 = None

from rdk_camera import RDKCamera, RDK_AVAILABLE


def main():
    cam_index = int(os.environ.get("ZONE_CAM_INDEX", "1"))
    width = 640
    height = 480
    crop_percentage = 0.45
    crop_height = int(height * crop_percentage)

    use_rdk = RDK_AVAILABLE and os.environ.get("USE_RDK_CAMERA", "1") == "1"
    if use_rdk:
        camera = RDKCamera(camera_index=cam_index, width=width, height=height)
    else:
        if Picamera2 is None:
            raise RuntimeError("Picamera2/libcamera not available. Set USE_RDK_CAMERA=1 for RDK MIPI.")
        camera = Picamera2(cam_index)
        camera.start()

    fps_time = time.perf_counter()
    counter = 0
    fps = 0

    try:
        while True:
            if use_rdk:
                frame = camera.read()
                if frame is None:
                    time.sleep(0.005)
                    continue
            else:
                frame = camera.capture_array()
            frame = frame[crop_height:, :]

            counter += 1
            if time.perf_counter() - fps_time > 1:
                fps = int(counter / (time.perf_counter() - fps_time))
                fps_time = time.perf_counter()
                counter = 0

            cv2.putText(
                frame,
                f"FPS: {fps}",
                (10, 20),
                cv2.FONT_HERSHEY_DUPLEX,
                0.5,
                (0, 255, 0),
                1,
                cv2.LINE_AA,
            )

            cv2.imshow("Zone Camera (test)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
    finally:
        if use_rdk:
            camera.close()
        else:
            camera.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
