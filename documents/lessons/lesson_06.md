# Lesson 6: Control Stability

Use this file as context to generate a 90-minute lesson plan.
Output should include: title, objective, prerequisites, 90-minute schedule (time blocks), activities, assessment, and homework.
Keep tools and examples aligned with the repo paths listed below.

## Objective
To achieve consistent and stable turning behavior using IMU-based yaw control.

## Learning outcomes
- Explain how turn_direction triggers turn state.
- Tune TURN_* parameters for 90/180 degree turns.
- Validate IMU-based stop condition for turns.

## Repo context
Use code from the Autobotic_v3 folder in this repository.

## Key files
- `robot_v.3/Python/Autobotic_v3/control.py`
- `robot_v.3/Python/Autobotic_v3/mp_manager.py`

## Key technical points
- TURN_USE_IMU and TURN_ANGLE_DEG define yaw-based stopping.
- TURN_COOLDOWN prevents rapid repeated turns.
- YAW_HOLD_GAIN stabilizes heading when line is lost.

## Suggested activities
- Simulate turn inputs by forcing turn_direction in mp_manager.
- Measure turn accuracy with a simple angle marker.
- Adjust TURN_IMU_TOL for consistent stop.

## Assessment ideas
- Short quiz or checklist based on outputs above.
- Student demo or log submission.
