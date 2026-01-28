# Lesson 5: Sensor Verification

Use this file as context to generate a 90-minute lesson plan.
Output should include: title, objective, prerequisites, 90-minute schedule (time blocks), activities, assessment, and homework.
Keep tools and examples aligned with the repo paths listed below.

## Objective
To validate sensor reliability and ensure accurate communication between hardware and software.

## Learning outcomes
- Verify IMU and IR values arrive in mp_manager.
- Confirm Arduino serial settings and port mapping.
- Identify common sensor noise and drift patterns.

## Repo context
Use code from the Autobotic_v3 folder in this repository.

## Key files
- `robot_v.3/Python/Autobotic_v3/sensor_serial.py`
- `robot_v.3/Python/Autobotic_v3/arduino_bridge.ino`
- `robot_v.3/Python/Autobotic_v3/mp_manager.py`

## Key technical points
- Arduino handles sensors and servos only; motor on Yahboom USB.
- imu_last_ts and ir_last_ts indicate freshness.
- Validate ttyACM0 for Arduino and ttyUSB0 for motor.

## Suggested activities
- Print IMU yaw/pitch/roll values during movement.
- Check IR values against obstacles at known distance.
- Confirm servo preset commands execute.

## Assessment ideas
- Short quiz or checklist based on outputs above.
- Student demo or log submission.
