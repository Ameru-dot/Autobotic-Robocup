# Lesson 4: Motor Performance Tuning

Use this file as context to generate a 90-minute lesson plan.
Output should include: title, objective, prerequisites, 90-minute schedule (time blocks), activities, assessment, and homework.
Keep tools and examples aligned with the repo paths listed below.

## Objective
To refine motor control for smooth, responsive, and precise robot movement.

## Learning outcomes
- Explain motor mapping M1-M4 and direction inversion.
- Tune control gains for stable speed and turning.
- Verify manual control responsiveness.

## Repo context
Use code from the Autobotic_v3 folder in this repository.

## Key files
- `robot_v.3/Python/Autobotic_v3/motor_serial.py`
- `robot_v.3/Python/Autobotic_v3/motor_driver.py`
- `robot_v.3/Python/Autobotic_v3/motor_control.py`
- `robot_v.3/Python/Autobotic_v3/control.py`
- `robot_v.3/Python/Autobotic_v3/manual_control.py`

## Key technical points
- MOTOR_ORDER and MOTOR_INVERT affect real wheel direction.
- control.py mixes vx/vy/omega into 4-wheel speeds.
- Smooth turns depend on KP_TURN and TURN_SPEED_GAIN.

## Suggested activities
- Confirm wheel directions using manual_control.py.
- Tune KP_TURN and VY_CMD for stable tracking.
- Log motor outputs during straight and turn.

## Assessment ideas
- Short quiz or checklist based on outputs above.
- Student demo or log submission.
