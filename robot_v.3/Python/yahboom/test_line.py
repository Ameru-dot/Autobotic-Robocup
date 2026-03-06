import os
import time

import cv2

try:
    from picamera2 import Picamera2
    from libcamera import controls
except Exception:
    Picamera2 = None
    controls = None

from rdk_camera import RDKCamera, RDK_AVAILABLE


def main():
    cam_index = int(os.environ.get("LINE_CAM_INDEX", "0"))
    width = 448
    height = 252

    use_rdk = RDK_AVAILABLE and os.environ.get("USE_RDK_CAMERA", "1") == "1"
    if use_rdk:
        camera = RDKCamera(camera_index=cam_index, width=width, height=height)
    else:
        if Picamera2 is None:
            raise RuntimeError("Picamera2/libcamera not available. Set USE_RDK_CAMERA=1 for RDK MIPI.")
        camera = Picamera2(cam_index)
        mode = camera.sensor_modes[0]
        camera.configure(camera.create_video_configuration(sensor={"output_size": mode["size"], "bit_depth": mode["bit_depth"]}))
        camera.start()
        try:
            camera.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 6.5})
        except Exception:
            pass
        time.sleep(0.1)

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
                if frame.shape[1] != width or frame.shape[0] != height:
                    frame = cv2.resize(frame, (width, height))
            else:
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
        if use_rdk:
            camera.close()
        else:
            camera.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
