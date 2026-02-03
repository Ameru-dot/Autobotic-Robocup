#!/usr/bin/env python3
"""
Send LED on/off commands to Arduino Mega over serial.
Requires Arduino running arduino_bridge.ino (expects: LED 1 / LED 0).
"""

import time
import sys
import serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"
BAUD = 115200


def send(cmd: str, ser: serial.Serial):
    ser.write((cmd.strip() + "\n").encode())
    time.sleep(0.05)
    if ser.in_waiting:
        try:
            print(ser.read(ser.in_waiting).decode(errors="ignore").strip())
        except Exception:
            pass


def main():
    print(f"Opening {PORT} @ {BAUD}...")
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        time.sleep(1)
        send("PING", ser)
        print("LED ON")
        send("LED 1", ser)
        time.sleep(1)
        print("LED OFF")
        send("LED 0", ser)
        print("Done")


if __name__ == "__main__":
    main()
