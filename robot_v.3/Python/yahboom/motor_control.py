import logging
import time

import motor

logger = logging.getLogger(__name__)


def log_event(message: str):
    logger.info(message)


def forward(speed=300):
    """Moves the robot forward."""
    motor.control_speed(speed, speed, speed, speed)


def backward(speed=400):
    """Moves the robot backward."""
    motor.control_speed(-speed, -speed, -speed, -speed)


def left(speed=300):
    """Turns the robot left."""
    motor.control_speed(0, 0, speed, speed)


def right(speed=300):
    """Turns the robot right."""
    motor.control_speed(speed, speed, 0, 0)


def spin_left(speed=700):
    """Spins the robot left."""
    motor.control_speed(-speed, -speed, speed, speed)


def spin_right(speed=700):
    """Spins the robot right."""
    motor.control_speed(speed, speed, -speed, -speed)


def brake():
    """Applies brakes to the robot."""
    print("Brake activated")
    motor.send_data("$upload:0,0,0#")
    motor.control_pwm(0, 0, 0, 0)
    time.sleep(0.05)
    motor.control_speed(0, 0, 0, 0)
    log_event("Brake activated")
