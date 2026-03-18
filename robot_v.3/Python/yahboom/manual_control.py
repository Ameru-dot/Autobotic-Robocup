"""
Manual keyboard control using pygame (shared-memory version).
Mapping aligned with manual_direct.py:
- W/S: forward/backward (vy)
- A/D: turn left/right (omega)
- Q/E: fine turn left/right (omega)
- Space: stop
- M: switch to manual objective
- Esc/quit: set terminate
"""

import pygame
from mp_manager import manual_vx, manual_vy, manual_omega, objective, terminate

BASE_SPEED = 0.5
TURN_SPEED = 0.6

# Optional quick direction fix without code edits
REV_FWD = False
REV_TURN = False


def manual_loop():
    pygame.init()
    pygame.display.set_mode((320, 200))
    pygame.display.set_caption("Manual Control")
    clock = pygame.time.Clock()

    objective.value = "manual"
    manual_vx.value = 0.0
    manual_vy.value = 0.0
    manual_omega.value = 0.0

    while not terminate.value:
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

        # Forward/backward
        if keys[pygame.K_w]:
            vy += BASE_SPEED
        if keys[pygame.K_s]:
            vy -= BASE_SPEED

        # Turn left/right
        if keys[pygame.K_a]:
            omega += TURN_SPEED
        if keys[pygame.K_d]:
            omega -= TURN_SPEED

        # Fine turn with Q/E
        if keys[pygame.K_q]:
            omega += TURN_SPEED * 0.5
        if keys[pygame.K_e]:
            omega -= TURN_SPEED * 0.5

        if REV_FWD:
            vy = -vy
        if REV_TURN:
            omega = -omega

        # Differential mode in control.py ignores vx; keep at 0 for clarity.
        manual_vx.value = 0.0
        manual_vy.value = vy
        manual_omega.value = omega

        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    manual_loop()
