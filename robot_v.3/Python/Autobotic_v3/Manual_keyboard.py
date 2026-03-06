import time
import serial
import pygame

PORT = "/dev/ttyACM0"
BAUD = 115200
SPEED = 150
SPEED1 = 200


def send(ser, m1, m2, m3, m4):
    cmd = f"M,{m1},{m2},{m3},{m4}\n"
    ser.write(cmd.encode())


pygame.init()
screen = pygame.display.set_mode((400, 200))
pygame.display.set_caption("Motor Control - WASD or Arrows")
font = pygame.font.Font(None, 36)


def draw_message(message):
    screen.fill((0, 0, 0))
    text = font.render(message, True, (255, 255, 255))
    screen.blit(text, (20, 80))
    pygame.display.flip()


def move_forward(ser):
    draw_message("Forward")
    send(ser, SPEED, SPEED, SPEED, SPEED)


def move_backward(ser):
    draw_message("Backward")
    send(ser, -SPEED, -SPEED, -SPEED, -SPEED)


def turn_left(ser):
    draw_message("Left")
    send(ser, -SPEED1, SPEED1, -SPEED, SPEED)


def turn_right(ser):
    draw_message("Right")
    send(ser, SPEED, -SPEED, SPEED, -SPEED)


def stop(ser):
    draw_message("Stopped")
    send(ser, 0, 0, 0, 0)


try:
    ser = serial.Serial(PORT, BAUD, timeout=0.5)
    time.sleep(1)
    draw_message("Ready - Use Arrow Keys or WASD")

    running = True
    while running:
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move_forward(ser)
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move_backward(ser)
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            turn_left(ser)
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            turn_right(ser)
        else:
            stop(ser)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        time.sleep(0.05)

except KeyboardInterrupt:
    pass

finally:
    try:
        stop(ser)
    except Exception:
        pass
    try:
        ser.close()
    except Exception:
        pass
    pygame.quit()
    print("Exited cleanly.")
