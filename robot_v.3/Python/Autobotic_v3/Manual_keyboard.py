import pygame
import time
from motor_driver import MotorDriver

# Initialize motor driver
md = MotorDriver(port="/dev/ttyUSB0", motor_type=1, upload_data=1)
SPEED = 300
SPEED1 = 600


# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((400, 200))
pygame.display.set_caption("Motor Control - WASD or Arrows")
font = pygame.font.Font(None, 36)

def draw_message(message):
    screen.fill((0, 0, 0))
    text = font.render(message, True, (255, 255, 255))
    screen.blit(text, (20, 80))
    pygame.display.flip()

def move_forward(): 
    draw_message("Forward")
    md.control_speed(SPEED, SPEED, SPEED, SPEED)

def move_backward(): 
    draw_message("Backward")
    md.control_speed(-SPEED, -SPEED, -SPEED, -SPEED)

def turn_left(): 
    draw_message("Left")
    md.control_speed(-SPEED1, SPEED1, -SPEED, SPEED)

def turn_right(): 
    draw_message("Right")
    md.control_speed(SPEED, -SPEED, SPEED, -SPEED)

def stop():
    draw_message("Stopped")
    md.control_speed(0, 0, 0, 0)

# Start
draw_message("Ready - Use Arrow Keys or WASD")

try:
    running = True
    while running:
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move_forward()
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move_backward()
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            turn_left()
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            turn_right()
        else:
            stop()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        time.sleep(0.05)

except KeyboardInterrupt:
    pass

finally:
    stop()
    md.close()
    pygame.quit()
    print("Exited cleanly.")


