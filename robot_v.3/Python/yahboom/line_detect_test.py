import line_cam
from mp_manager import objective, terminate


def main():
    line_cam.debug_mode = True
    objective.value = "follow_line"
    terminate.value = False
    line_cam.line_cam_loop()


if __name__ == "__main__":
    main()
