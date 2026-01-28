import os
import time

import cv2


def main():
    device = os.environ.get("LINE_CAM_DEVICE", "/dev/video0")
    cap = cv2.VideoCapture(device)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open line camera at {device}")

    width = 448
    height = 252
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
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
