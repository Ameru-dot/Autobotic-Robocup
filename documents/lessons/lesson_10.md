# Lesson 10: Zone & Ball Execution

Use this file as context to generate a 90-minute lesson plan.
Output should include: title, objective, prerequisites, 90-minute schedule (time blocks), activities, assessment, and homework.
Keep tools and examples aligned with the repo paths listed below.

## Objective
To optimize ball detection, pickup, and drop performance during zone tasks.

## Learning outcomes
- Explain how zone_cam selects and filters detections.
- Tune ball thresholds and confidence filtering.
- Verify drop alignment using green/red corners.

## Repo context
Use code from the Autobotic_v3 folder in this repository.

## Key files
- `robot_v.3/Python/Autobotic_v3/zone_cam.py`
- `robot_v.3/Python/Autobotic_v3/control.py`
- `robot_v.3/Ai/models/ball_zone_s/ball_detect_s_edgetpu.tflite`

## Key technical points
- ball_error_x drives strafe correction.
- zone_status controls detect vs deposit modes.
- corner_distance is used for drop alignment.

## Suggested activities
- Test detection with sample balls at varying distances.
- Adjust BALL_CONF_MIN and BALL_WIDTH_THRESH.
- Simulate deposit_green and deposit_red modes.

## Assessment ideas
- Short quiz or checklist based on outputs above.
- Student demo or log submission.
