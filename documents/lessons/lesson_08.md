# Lesson 8: Camera & Vision Stability

Use this file as context to generate a 90-minute lesson plan.
Output should include: title, objective, prerequisites, 90-minute schedule (time blocks), activities, assessment, and homework.
Keep tools and examples aligned with the repo paths listed below.

## Objective
To improve vision accuracy by optimizing camera placement and minimizing vibration effects.

## Learning outcomes
- Validate camera device mapping and resolution.
- Measure FPS under different lighting conditions.
- Confirm cropping and ROI behavior in code.

## Repo context
Use code from the Autobotic_v3 folder in this repository.

## Key files
- `robot_v.3/Python/Autobotic_v3/test_line.py`
- `robot_v.3/Python/Autobotic_v3/zone_test.py`
- `robot_v.3/Python/Autobotic_v3/line_cam.py`
- `robot_v.3/Python/Autobotic_v3/zone_cam.py`

## Key technical points
- LINE_CAM_DEVICE and ZONE_CAM_DEVICE select /dev/video*.
- Zone camera uses lower crop for ball detection.
- Resizing affects FPS and detection stability.

## Suggested activities
- Run test_line.py and zone_test.py to confirm feeds.
- Adjust camera angle to reduce line jitter.
- Record FPS changes with different resolutions.

## Assessment ideas
- Short quiz or checklist based on outputs above.
- Student demo or log submission.
