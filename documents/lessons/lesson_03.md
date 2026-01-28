# Lesson 3: Line & Marker Optimization

Use this file as context to generate a 90-minute lesson plan.
Output should include: title, objective, prerequisites, 90-minute schedule (time blocks), activities, assessment, and homework.
Keep tools and examples aligned with the repo paths listed below.

## Objective
To optimize line following and marker-based decision making for stable and accurate navigation.

## Learning outcomes
- Describe the line detection pipeline and key thresholds.
- Tune green marker detection for left/right/turn-around.
- Validate line_error_x and turn_direction outputs.

## Repo context
Use code from the Autobotic_v3 folder in this repository.

## Key files
- `robot_v.3/Python/Autobotic_v3/line_cam.py`
- `robot_v.3/Python/Autobotic_v3/config.ini`
- `robot_v.3/Python/Autobotic_v3/line_detect_test.py`
- `robot_v.3/Python/Autobotic_v3/test_line.py`

## Key technical points
- line_cam.py generates line_error_x and turn_direction.
- config.ini stores color thresholds for black/green/red.
- Check marker placement rules: ignore markers too low.

## Suggested activities
- Run line_detect_test.py and observe detection stability.
- Adjust green_min/green_max for markers and re-test.
- Record line_error_x range on straight and curved lines.

## Assessment ideas
- Short quiz or checklist based on outputs above.
- Student demo or log submission.
