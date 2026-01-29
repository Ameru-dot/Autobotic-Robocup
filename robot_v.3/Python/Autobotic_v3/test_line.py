import os
import time

import cv2
from libcamera import controls
from picamera2 import Picamera2


def main():
    cam_index = int(os.environ.get("LINE_CAM_INDEX", "0"))
    camera = Picamera2(cam_index)

    mode = camera.sensor_modes[0]
    camera.configure(camera.create_video_configuration(sensor={"output_size": mode["size"], "bit_depth": mode["bit_depth"]}))
    camera.start()
    try:
        camera.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 6.5})
    except Exception:
        pass
    time.sleep(0.1)

    width = 448
    height = 252

    fps_time = time.perf_counter()
    counter = 0
    fps = 0

    try:
        while True:
            frame = camera.capture_array()
            frame = cv2.resize(frame, (width, height))
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

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

            cv2.imshow("Line Camera (test)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
    finally:
        camera.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
