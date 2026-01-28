import os
import time

import cv2


def main():
    device = os.environ.get("ZONE_CAM_DEVICE", "/dev/video2")
    cap = cv2.VideoCapture(device)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open zone camera at {device}")

    width = 640
    height = 480
    crop_percentage = 0.45
    crop_height = int(height * crop_percentage)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    fps_time = time.perf_counter()
    counter = 0
    fps = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            frame = cv2.resize(frame, (width, height))
            cropped = frame[crop_height:, :]

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
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
