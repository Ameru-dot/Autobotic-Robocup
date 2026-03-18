"""
Manual keyboard control (direct motor control).
- W/S: forward/backward (vy)
- A/D: strafe left/right (vx)
- Q/E: rotate left/right (omega)
- Space: stop
- Esc/quit: exit

This version sends motor speeds directly to Yahboom via motor.py
(no control.py / motor_serial.py required).
"""

import math
import os
import pygame
import motor

# Tunable speeds
BASE_SPEED = 0.6   # linear command 0..1
ROT_SPEED = 0.6    # rotation command 0..1
SPEED_MAX = 700    # motor command magnitude (Yahboom: -1000..1000)

# Omni geometry (same as control.py)
WHEEL_ANGLES_DEG = {"fl": 45, "fr": -45, "bl": 135, "br": -135}
ROBOT_RADIUS = 0.12

# Keep direct manual mapping consistent with motor_serial.py / main control:
# logical wheels -> Yahboom M1..M4
MOTOR_ORDER = ("fl", "bl", "fr", "br")
MOTOR_INVERT = {
    "fl": os.environ.get("INV_FL", "0") == "1",
    "fr": os.environ.get("INV_FR", "0") == "1",
    "bl": os.environ.get("INV_BL", "0") == "1",
    "br": os.environ.get("INV_BR", "0") == "1",
}

def mix_omni(vx: float, vy: float, omega: float):
    ang = {k: math.radians(v) for k, v in WHEEL_ANGLES_DEG.items()}
    raw = {
        "fl": -math.sin(ang["fl"]) * vx + math.cos(ang["fl"]) * vy + ROBOT_RADIUS * omega,
        "fr": -math.sin(ang["fr"]) * vx + math.cos(ang["fr"]) * vy + ROBOT_RADIUS * omega,
        "bl": -math.sin(ang["bl"]) * vx + math.cos(ang["bl"]) * vy + ROBOT_RADIUS * omega,
        "br": -math.sin(ang["br"]) * vx + math.cos(ang["br"]) * vy + ROBOT_RADIUS * omega,
    }
    max_mag = max(1.0, max(abs(v) for v in raw.values()))
    return {k: v / max_mag for k, v in raw.items()}

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
    screen = pygame.display.set_mode((320, 200))
    pygame.display.set_caption("Manual Control (Direct)")
    clock = pygame.time.Clock()

    running = True
    while running:
        vx = 0.0
        vy = 0.0
        omega = 0.0

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
            vy += BASE_SPEED
        if keys[pygame.K_s]:
            vy -= BASE_SPEED
        if keys[pygame.K_a]:
            vx -= BASE_SPEED
        if keys[pygame.K_d]:
            vx += BASE_SPEED
        if keys[pygame.K_q]:
            omega += ROT_SPEED
        if keys[pygame.K_e]:
            omega -= ROT_SPEED

        speeds = mix_omni(vx, vy, omega)
        fl = int(SPEED_MAX * speeds["fl"])
        fr = int(SPEED_MAX * speeds["fr"])
        bl = int(SPEED_MAX * speeds["bl"])
        br = int(SPEED_MAX * speeds["br"])
        send_wheels(fl, fr, bl, br)

        clock.tick(30)

    send_wheels(0, 0, 0, 0)
    pygame.quit()


if __name__ == "__main__":
    main()
