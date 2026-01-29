import os
import time

import cv2
from picamera2 import Picamera2


def main():
    cam_index = int(os.environ.get("ZONE_CAM_INDEX", "1"))
    camera = Picamera2(cam_index)
    camera.start()

    width = 640
    height = 480
    crop_percentage = 0.45
    crop_height = int(height * crop_percentage)

    fps_time = time.perf_counter()
    counter = 0
    fps = 0

    try:
        while True:
            frame = camera.capture_array()
            frame = cv2.resize(frame, (width, height))
            cropped = frame[crop_height:, :]
            cropped = cv2.cvtColor(cropped, cv2.COLOR_RGBA2BGR)

            counter += 1
            if time.perf_counter() - fps_time > 1:
                fps = int(counter / (time.perf_counter() - fps_time))
                fps_time = time.perf_counter()
                counter = 0

            cv2.putText(
                cropped,
                f"FPS: {fps}",
                (10, 20),
                cv2.FONT_HERSHEY_DUPLEX,
                0.5,
                (0, 255, 0),
                1,
                cv2.LINE_AA,
            )

            cv2.imshow("Zone Camera (test)", cropped)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
    finally:
        camera.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
