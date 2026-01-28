# Lesson 2: Software Architecture

Use this file as context to generate a 90-minute lesson plan.
Output should include: title, objective, prerequisites, 90-minute schedule (time blocks), activities, assessment, and homework.
Keep tools and examples aligned with the repo paths listed below.

## Objective
To understand how the existing robot software system operates and how processes communicate with each other.

## Learning outcomes
- Explain the purpose of each process in main.py.
- Describe how mp_manager.py shares state between processes.
- Draw a data-flow diagram from cameras to motor commands.

## Repo context
Use code from the Autobotic_v3 folder in this repository.

## Key files
- `robot_v.3/Python/Autobotic_v3/main.py`
- `robot_v.3/Python/Autobotic_v3/mp_manager.py`
- `robot_v.3/Python/Autobotic_v3/line_cam.py`
- `robot_v.3/Python/Autobotic_v3/zone_cam.py`
- `robot_v.3/Python/Autobotic_v3/control.py`
- `robot_v.3/Python/Autobotic_v3/motor_serial.py`
- `robot_v.3/Python/Autobotic_v3/sensor_serial.py`

## Key technical points
- Multiprocessing isolates camera, control, and IO loops.
- mp_manager values are the interface between perception and control.
- main_test.py can run without hardware for safe validation.

## Suggested activities
- Sketch process diagram and mark inputs/outputs.
- Trace one variable (line_error_x) end-to-end.
- Discuss failure modes when one process crashes.

## Assessment ideas
- Short quiz or checklist based on outputs above.
- Student demo or log submission.
