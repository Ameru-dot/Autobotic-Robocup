"""
Manual keyboard control using pygame.
- W/S: forward/backward (vy)
- A/D: strafe left/right (vx)
- Q/E: rotate left/right (omega)
- Space: stop
- M: switch to manual objective
- Esc/quit: set terminate
"""

import pygame
from mp_manager import manual_vx, manual_vy, manual_omega, objective, terminate

BASE_SPEED = 0.5
ROT_SPEED = 0.6


def manual_loop():
    pygame.init()
    screen = pygame.display.set_mode((320, 200))
    pygame.display.set_caption("Manual Control")
    clock = pygame.time.Clock()

    objective.value = "manual"
    manual_vx.value = 0.0
    manual_vy.value = 0.0
    manual_omega.value = 0.0

    while not terminate.value:
        vx = 0.0
        vy = 0.0
        omega = 0.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate.value = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    terminate.value = True
                if event.key == pygame.K_m:
                    objective.value = "manual"
                if event.key == pygame.K_SPACE:
                    manual_vx.value = 0.0
                    manual_vy.value = 0.0
                    manual_omega.value = 0.0

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

        manual_vx.value = vx
        manual_vy.value = vy
        manual_omega.value = omega

        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    manual_loop()
