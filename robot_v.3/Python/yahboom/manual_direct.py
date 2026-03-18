"""
Manual keyboard control (direct motor control).
- W/S: forward/backward
- A/D: turn left/right
- Q/E: fine turn left/right
- Space: stop
- Esc/quit: exit

This version sends motor speeds directly to Yahboom via motor.py
(no control.py / motor_serial.py required).
"""

import os

import pygame
import motor

# Tunable speeds (Yahboom range: -1000..1000)
BASE_SPEED = 650
TURN_SPEED = 550

# Keep direct manual mapping consistent with motor_serial.py / main control:
# logical wheels -> Yahboom M1..M4
MOTOR_ORDER = ("fl", "bl", "fr", "br")
MOTOR_INVERT = {
    "fl": os.environ.get("INV_FL", "0") == "1",
    "fr": os.environ.get("INV_FR", "0") == "1",
    "bl": os.environ.get("INV_BL", "0") == "1",
    "br": os.environ.get("INV_BR", "0") == "1",
}


def send_wheels(fl: int, fr: int, bl: int, br: int):
    values = {"fl": fl, "fr": fr, "bl": bl, "br": br}
    ordered = []
    for key in MOTOR_ORDER:
        val = values[key]
        if MOTOR_INVERT.get(key, False):
            val = -val
        ordered.append(val)
    motor.control_speed(*ordered)


def main():
    pygame.init()
    pygame.display.set_mode((320, 200))
    pygame.display.set_caption("Manual Control (Direct)")
    clock = pygame.time.Clock()

    running = True
    while running:
        left_cmd = 0
        right_cmd = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    send_wheels(0, 0, 0, 0)

        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            left_cmd += BASE_SPEED
            right_cmd += BASE_SPEED
        elif keys[pygame.K_s]:
            left_cmd -= BASE_SPEED
            right_cmd -= BASE_SPEED

        # A: turn left, D: turn right
        if keys[pygame.K_a]:
            left_cmd -= TURN_SPEED
            right_cmd += TURN_SPEED
        elif keys[pygame.K_d]:
            left_cmd += TURN_SPEED
            right_cmd -= TURN_SPEED

        # Optional fine turn with Q/E
        if keys[pygame.K_q]:
            left_cmd -= TURN_SPEED // 2
            right_cmd += TURN_SPEED // 2
        elif keys[pygame.K_e]:
            left_cmd += TURN_SPEED // 2
            right_cmd -= TURN_SPEED // 2

        left_cmd = max(-1000, min(1000, left_cmd))
        right_cmd = max(-1000, min(1000, right_cmd))

        # left wheels: fl/bl, right wheels: fr/br
        send_wheels(left_cmd, right_cmd, left_cmd, right_cmd)
        clock.tick(30)

    send_wheels(0, 0, 0, 0)
    pygame.quit()


if __name__ == "__main__":
    main()
