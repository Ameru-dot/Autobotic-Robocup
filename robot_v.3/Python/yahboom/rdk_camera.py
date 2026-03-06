import os
import time

import cv2
import numpy as np

try:
    from hobot_vio import libsrcampy as srcampy
except Exception:
    srcampy = None

RDK_AVAILABLE = srcampy is not None


class RDKCamera:
    def __init__(
        self,
        camera_index: int = -1,
        width: int = 640,
        height: int = 480,
        fps: int = -1,
        sensor_width: int | None = None,
        sensor_height: int | None = None,
        pipe_id: int | None = None,
    ):
        if not RDK_AVAILABLE:
            raise RuntimeError("hobot_vio.libsrcampy not available on this system")

        self.width = int(width)
        self.height = int(height)

        # Ensure even dimensions for NV12
        if self.width % 2:
            self.width += 1
        if self.height % 2:
            self.height += 1

        self.sensor_width = int(sensor_width or os.environ.get("RDK_SENSOR_WIDTH", 1920))
        self.sensor_height = int(sensor_height or os.environ.get("RDK_SENSOR_HEIGHT", 1080))
        self.pipe_id = int(pipe_id or os.environ.get("RDK_PIPE_ID", 0))

        self.cam = srcampy.Camera()
        # open_cam(pipe_id, video_index, fps, [w, disp_w], [h, disp_h], sensor_h, sensor_w)
        self.cam.open_cam(
            self.pipe_id,
            int(camera_index),
            int(fps),
            [self.width, self.width],
            [self.height, self.height],
            self.sensor_height,
            self.sensor_width,
        )
        time.sleep(0.1)

    def read(self):
        buf = self.cam.get_img(2, self.width, self.height)
        if buf is None:
            return None
        arr = np.frombuffer(buf, dtype=np.uint8)
        expected = self.width * self.height * 3 // 2
        if arr.size < expected:
            return None
        frame_nv12 = arr[:expected].reshape((self.height * 3 // 2, self.width))
        bgr = cv2.cvtColor(frame_nv12, cv2.COLOR_YUV2BGR_NV12)
        return bgr

    def close(self):
        try:
            self.cam.close_cam()
        except Exception:
            pass
