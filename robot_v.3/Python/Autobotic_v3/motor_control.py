import logging
import time

from motor import MotorDriver

logger = logging.getLogger(__name__)

md = MotorDriver(port="/dev/ttyUSB0", baudrate=115200, motor_type=2, upload_data=1)


def log_event(message: str):
    logger.info(message)


def forward(speed=300):
    """Moves the robot forward."""
    md.control_speed(speed, speed, speed, speed)


def backward(speed=400):
    """Moves the robot backward."""
    md.control_speed(-speed, -speed, -speed, -speed)


def left(speed=300):
    """Turns the robot left."""
    md.control_speed(0, 0, speed, speed)


def right(speed=300):
    """Turns the robot right."""
    md.control_speed(speed, speed, 0, 0)


def spin_left(speed=700):
    """Spins the robot left."""
    md.control_speed(-speed, -speed, speed, speed)


def spin_right(speed=700):
    """Spins the robot right."""
    md.control_speed(speed, speed, -speed, -speed)


def brake():
    """Applies brakes to the robot."""
    print("Brake activated")
    md.send_data("$upload:0,0,0#")
    md.control_pwm(0, 0, 0, 0)
    time.sleep(0.05)
    md.control_speed(0, 0, 0, 0)
    log_event("Brake activated")
