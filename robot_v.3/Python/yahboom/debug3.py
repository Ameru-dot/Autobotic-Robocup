import cv2
import torch
import numpy as np
import time
import datetime
from multiprocessing import Process, Value
from motor_driver import MotorDriver 
from multiprocessing import current_process # Import for clearer logging

# Import YOLO from ultralytics for YOLOv8 model
from ultralytics import YOLO 

# === KONFIGURASI LALUAN KAMERA ===
# Sila gantikan nilai placeholder di bawah dengan laluan kamera sebenar anda.
# Anda boleh mencari laluan ini dengan menjalankan 'ls -l /dev/v4l/by-id/' atau 'ls -l /dev/v4l/by-path/' di terminal.
# Contoh: "/dev/v4l/by-id/usb-Logitech_Webcam_C920_ABCDEF12-video-index0"
CAMERA_PATH_DOWN = "/dev/video0" # Gantikan dengan laluan kamera bawah anda yang stabil
CAMERA_PATH_FRONT = "/dev/video2" # Gantikan dengan laluan kamera depan anda yang stabil
# Jika anda tidak pasti, mulakan dengan /dev/video0, /dev/video1, dan sebagainya,
# dan gantikan dengan laluan by-id/by-path setelah anda mengenal pastinya.

# === HSV Thresholds Centralized ===
HSV_THRESHOLDS = {
    "black": (np.array([0, 0, 0]), np.array([180, 255, 50])), # Original for general black detection
    "line_follow_black": (np.array([0, 0, 0]), np.array([179, 255, 76])), # Specific for line following
    "green": (np.array([23, 74, 0]), np.array([50, 255, 255])),
    "silver": (np.array([105, 118, 0]), np.array([141, 255, 255])),
    "red1": (np.array([0, 100, 100]), np.array([10, 255, 255])),
    "red2": (np.array([160, 100, 100]), np.array([180, 255, 255])),
    "green_zone": (np.array([69, 71, 0]), np.array([98, 255, 255]))
}

# === Logging Utility ===
def log_event(message):
    """Logs an event with a timestamp to a file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("robot_log.txt", "a") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")

# Initialize MotorDriver (now using your actual MotorDriver)
md = MotorDriver(port="/dev/ttyUSB0", motor_type=2, upload_data=1) 

# === Servo Actions (Skeleton) ===
def grip_ball():
    """Simulates gripping a ball with the servo."""
    print("Ã°Å¸Â¤â€“ Gripping ball (servo command)")
    log_event("Gripped ball")

def release_ball():
    """Simulates releasing a ball with the servo."""
    print("Ã°Å¸â€“ Releasing ball (servo command)")
    log_event("Released ball")

# === Motor Control Functions ===
def forward(speed=300):
    """Moves the robot forward."""
    md.control_speed(speed, speed, speed, speed)
    # print(f"Moving forward at speed {speed}") # Commented out for cleaner console during operation

def backward(speed=400):
    """Moves the robot backward."""
    md.control_speed(-speed, -speed, -speed, -speed)
    # print(f"Moving backward at speed {speed}")

def left(speed=300):
    """Turns the robot left."""
    md.control_speed(0, 0, speed, speed)
    # print(f"Turning left at speed {speed}")

def right(speed=300):
    """Turns the robot right."""
    md.control_speed(speed, speed, 0, 0)
    # print(f"Turning right at speed {speed}")

def spin_left(speed=700):
    """Spins the robot left."""
    md.control_speed(-speed, -speed, speed, speed)
    # print(f"Spinning left at speed {speed}")

def spin_right(speed=700):
    """Spins the robot right."""
    md.control_speed(speed, speed, -speed, -speed)
    # print(f"Spinning right at speed {speed}")

def brake():
    """Applies brakes to the robot."""
    print("Brake activated") # Keep this print for critical action
    md.send_data("$upload:0,0,0#")
    md.control_pwm(0, 0, 0, 0)
    time.sleep(0.05)
    md.control_speed(0, 0, 0, 0)
    log_event("Brake activated")

# === Process 1: Follow Line and Green Direction ===
def line_navigator(active_flag, rescue_flag, exit_flag, terminate_flag):
    """
    Navigates the robot along a black line, detects green marks for turns,
    and identifies silver zones to trigger the rescue process.
    """
    # Gunakan laluan kamera yang stabil
    cap_down = cv2.VideoCapture(CAMERA_PATH_DOWN)
    if not cap_down.isOpened():
        print(f"Ã¢ÂÅ’ Kamera bawah gagal dibuka dari {CAMERA_PATH_DOWN}.")
        log_event(f"Error: Downward camera failed to open from {CAMERA_PATH_DOWN}.")
        return
    time.sleep(2) # Allow camera to warm up
    print("Ã°Å¸Å¸Â¢ Line navigator process started")
    log_event("Line navigator process started")
    # Adjusted durations and speeds for green mark turns
    SINGLE_MARKER_TURN_DURATION = 0.8 # Duration for a small adjustment turn
    U_TURN_DURATION_BOTH = 0.5 # Duration for a full 180 degree U-turn
    TURN_SPEED = 700 # Speed for turns induced by green markers
    
    # --- P-Controller constants ---
    BASE_SPEED = 300 # Kelajuan asas untuk bergerak ke hadapan
    KP = 6.5      # Proportional Gain - nilai yang perlu diubah suai (tune)
    
    # --- Last Seen Variables for Line Following ---
    last_seen_cx = None  # Stores the last known X position of the line's centroid
    # How many frames the line can be missing before robot performs a recovery action
    LOST_LINE_THRESHOLD_FRAMES = 200 # Increased for more robustness
    lost_line_counter = 0 # Counts frames where line is not detected
    current_action_text = "Mencari Garisan..." # Default action text for debug display
    while True:
        if terminate_flag.value: # Check for termination signal
            print(f"{current_process().name}: Menerima isyarat penamatan. Menutup...")
            log_event(f"{current_process().name}: Received termination signal. Shutting down gracefully.")
            break # Exit the loop gracefully
        # Check flags to determine current state and if navigation should continue
        if not active_flag.value or rescue_flag.value or exit_flag.value:
            brake()
            current_action_text = "Berhenti (Menunggu)"
            if exit_flag.value: # If exiting, this process should stop
                print("Line navigator stopping due to exit flag.")
                break
            # Update debug view even when paused/stopped
            # This ensures the last frame and status are visible
            ret, frame = cap_down.read()
            if ret:
                frame_resized = cv2.resize(frame, (320, 240))
                
                # Define ROI for line following.
                roi_start_y = 100 # Y-coordinate where ROI starts
                roi_end_y = 240   # Y-coordinate where ROI ends (bottom of frame)
                roi_display_only = frame_resized[roi_start_y:roi_end_y, :].copy() # For display purposes
                # Tambah teks status pada paparan debug
                cv2.putText(roi_display_only, f"Status: PAUSED", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                cv2.putText(roi_display_only, f"Active: {active_flag.value}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(roi_display_only, f"Rescue: {rescue_flag.value}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(roi_display_only, f"Exit: {exit_flag.value}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(roi_display_only, f"Tindakan: {current_action_text}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                # Create dummy masks for consistent hstack structure when paused
                dummy_mask_bgr = np.zeros((frame.shape[0], frame.shape[1] // 3, 3), dtype=np.uint8) # Approx width
                cv2.putText(dummy_mask_bgr, "PAUSED", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Resize roi_display_only to full frame height for stacking
                roi_display_only_resized = cv2.resize(roi_display_only, (roi_display_only.shape[1], frame.shape[0]))
                combined_debug_view = np.hstack((roi_display_only_resized, dummy_mask_bgr, dummy_mask_bgr, dummy_mask_bgr)) # Added one more dummy mask for silver
                cv2.imshow("Paparan Debug Kawalan Robot", combined_debug_view)
                
                # Tambahan: Throttling paparan untuk mengelakkan lag
                time.sleep(0.01)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Paparan debug ditutup oleh pengguna.")
                    log_event("Navigasi Garisan debug window closed.")
                    break # Exit loop if debug window is closed
            time.sleep(0.1) # Small delay to prevent busy-waiting when paused
            continue
        ret, frame = cap_down.read()
        if not ret:
            print("Camera 1 failed to read frame.")
            log_event("Error: Camera 1 failed to read frame.")
            break
        frame_resized = cv2.resize(frame, (320, 240))
        
        # Define ROI for line following.
        roi_start_y = 100 # Y-coordinate where ROI starts (from previous "last seen" code)
        roi_end_y = 240   # Y-coordinate where ROI ends (bottom of frame)
        roi = frame_resized[roi_start_y:roi_end_y, :] # Region of Interest for line detection
        # Create a copy of the full frame for drawing all debug overlays
        debug_display_frame = frame_resized.copy()
        # --- Silver Zone Detection (to trigger rescue mode) ---
        lower_silver, upper_silver = HSV_THRESHOLDS["silver"]
        hsv_full_frame = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2HSV)
        mask_silver = cv2.inRange(hsv_full_frame, lower_silver, upper_silver)
        # Draw silver mask on debug display
        mask_silver_bgr = cv2.cvtColor(mask_silver, cv2.COLOR_GRAY2BGR)
        cv2.putText(mask_silver_bgr, "Mask Perak", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        if cv2.countNonZero(mask_silver) > 500: # Threshold for silver zone presence (adjust as needed)
            current_action_text = "Zon Perak Dikesan! Mengaktifkan Mod Penyelamat..."
            print("Ã¢Å¡Âª Silver zone detected! Activating rescue mode.")
            log_event("Silver zone detected. Activating rescue mode.")
            active_flag.value = False # Pause line navigation
            rescue_flag.value = True  # Activate victim rescue
            brake() # Stop robot before transitioning
            time.sleep(1) # Give a moment for transition
            continue # Continue loop to re-evaluate flags, will now enter paused state
        # --- Green Mark Detection ---
        hsv_green = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower_green = HSV_THRESHOLDS["green_zone"][0] 
        upper_green = HSV_THRESHOLDS["green_zone"][1]
        mask_green = cv2.inRange(hsv_green, lower_green, upper_green)
        contours_green, _ = cv2.findContours(mask_green, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        green_marker_positions = []
        for cnt in contours_green:
            area = cv2.contourArea(cnt)
            if area > 100: # Smaller threshold for individual markers
                M_green = cv2.moments(cnt)
                if M_green["m00"] > 0:
                    cx_green_roi = int(M_green["m10"] / M_green["m00"])
                    green_marker_positions.append(cx_green_roi)
                    # Draw green marker bounding box on debug_display_frame (full frame coordinates)
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(debug_display_frame, (x, y + roi_start_y), (x + w, y + h + roi_start_y), (0, 255, 0), 2)
                    cv2.putText(debug_display_frame, "Green", (x, y + roi_start_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        # --- Black Line Detection ---
        lower_line, upper_line = HSV_THRESHOLDS["line_follow_black"]
        hsv_line = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        thresh_line = cv2.inRange(hsv_line, lower_line, upper_line)
        M_line = cv2.moments(thresh_line)
        
        # Initialize cx_line_full_frame outside the if block
        cx_line_full_frame = -1 
        line_detected_current_frame = False
        if M_line["m00"] > 0: # If a black line is detected
            cx_line_roi = int(M_line["m10"] / M_line["m00"])
            cx_line_full_frame = cx_line_roi # X-coordinate is the same for full frame
            line_detected_current_frame = True
            last_seen_cx = cx_line_full_frame # Update last seen position
            lost_line_counter = 0 # Reset counter if line is seen
            # Draw line debug overlays on debug_display_frame
            center_frame_x = frame_resized.shape[1] // 2 
            cv2.line(debug_display_frame, (center_frame_x, roi_start_y), (center_frame_x, roi_end_y), (255, 255, 0), 2)
            cv2.rectangle(debug_display_frame, (cx_line_full_frame - 5, roi_start_y), (cx_line_full_frame + 5, roi_start_y + 10), (0, 255, 0), 2)
            cv2.line(debug_display_frame, (center_frame_x, roi_start_y + roi.shape[0] // 2), (cx_line_full_frame, roi_start_y + roi.shape[0] // 2), (0, 255, 255), 1)
            
            # === BAHAGIAN BARU: Logik P-Controller untuk mengikut garisan ===
            # Kira ralat (error) - jarak garisan dari pusat
            error = center_frame_x - cx_line_full_frame
            
            # Kira kelajuan pusing (turn speed) berdasarkan ralat
            turn_speed = int(error * KP)
            
            # Kelajuan motor kiri dan kanan
            left_speed = BASE_SPEED - turn_speed
            right_speed = BASE_SPEED + turn_speed
            
            # Pastikan kelajuan berada dalam julat yang munasabah (cth. -600 hingga 600)
            left_speed = np.clip(left_speed, -600, 600)
            right_speed = np.clip(right_speed, -600, 600)
            
            current_action_text = f"Mengikut Garisan P-Control (Error: {error})"
            md.control_speed(left_speed, left_speed, right_speed, right_speed)
            
        else: # If no black line is detected in the current frame (LOST LINE recovery)
            lost_line_counter += 1
            if last_seen_cx is not None and lost_line_counter < LOST_LINE_THRESHOLD_FRAMES:
                # Continue movement based on the last known line position
                current_action_text = f"Garisan Hilang ({lost_line_counter}/{LOST_LINE_THRESHOLD_FRAMES}) - Mengikut Last Seen: {last_seen_cx}"
                if last_seen_cx < frame_resized.shape[1] // 2: # If last seen line was on the left, continue turning left
                    spin_left(300) # Slower spin to find line
                else: # If last seen line was on the right, continue turning right
                    spin_right(300) # Slower spin to find line
            else:
                # If line is lost for too long or never seen, perform a recovery action
                current_action_text = "Garisan Hilang Terlalu Lama! Melakukan Pemulihan..."
                print("Ã¢ÂÅ’ Tiada garis dikesan (lama) atau tidak pernah dikesan. Melakukan pemulihan.")
                log_event("Line lost for too long. Initiating recovery.")
                backward(200) # Move backward
                time.sleep(0.7) # For a short duration
                brake() # Stop
                spin_right(300) # Spin to try and find the line
                time.sleep(1.0)
                brake()
                last_seen_cx = None # Reset last_seen_cx to indicate complete loss for next recovery attempt
                lost_line_counter = 0 # Reset counter after recovery attempt
        # --- Green Marker Decision Logic (Relative to Black Line) ---
        # This logic takes precedence over line following if green markers are detected.
        # It will override any line following action taken in the same frame.
        if len(green_marker_positions) > 0 and line_detected_current_frame: # Ensure black line is also detected
            
            left_marker_relative_count = 0
            right_marker_relative_count = 0
            
            # Determine relative position of green markers to the black line
            for pos_roi in green_marker_positions:
                # Tolerance to consider it 'on' the line vs. left/right
                tolerance_from_line = 20 # Adjust this value as needed
                if pos_roi < cx_line_full_frame - tolerance_from_line:
                    left_marker_relative_count += 1
                elif pos_roi > cx_line_full_frame + tolerance_from_line:
                    right_marker_relative_count += 1
            
            # Action based on green marker detection relative to black line
            if left_marker_relative_count >= 1 and right_marker_relative_count >= 1:
                current_action_text = "U-Turn 180 Darjah (Dua Marker Hijau, Relatif Garisan)"
                print("Ã¢Å“â€¦ Kedua-dua marker hijau dikesan relatif kepada garisan - Melakukan U-turn 180 darjah!")
                log_event("Two green markers detected relative to line. Performing 180-degree U-turn.")
                brake()
                spin_right(TURN_SPEED) # Full spin right for 180 (adjust speed as needed)
                time.sleep(U_TURN_DURATION_BOTH) # Adjust duration for 180 turn
                brake()
                backward(300)
                time.sleep(0.3)
                brake()
                last_seen_cx = None # Reset after major turn
                lost_line_counter = 0 # Reset after major turn
            elif left_marker_relative_count >= 1:
                current_action_text = "Pembetulan Kiri (Marker Hijau Kiri Relatif Garisan)"
                print("Ã°Å¸Å¸Â© Marker hijau dikesan di kiri garisan - Melaraskan ke kiri.")
                log_event("Left green marker detected relative to line. Adjusting left.")
                brake()
                forward(300) # Move slightly forward to clear the marker and re-engage line
                time.sleep(0.4)
                brake()
                spin_left(900) # Use TURN_SPEED for stronger adjustment
                time.sleep(0.3) # Adjust duration for small turn
                brake()
                #forward(300) # Move slightly forward to clear the marker and re-engage line
                #time.sleep(0.5)
                #brake()
                last_seen_cx = None # Reset after adjustment to force re-detection of line
                lost_line_counter = 0 # Reset
            elif right_marker_relative_count >= 1:
                current_action_text = "Pembetulan Kanan (Marker Hijau Kanan Relatif Garisan)"
                print("Ã°Å¸Å¸Â© Marker hijau dikesan di kanan garisan - Melaraskan ke kanan.")
                log_event("Right green marker detected relative to line. Adjusting right.")
                brake()
                forward(300) # Move slightly forward to clear the marker and re-engage line
                time.sleep(0.4)
                brake()
                spin_right(900) # Use TURN_SPEED for stronger adjustment
                time.sleep(0.3) # Adjust duration for small turn
                brake()
                #forward(300) # Move slightly forward to clear the marker and re-engage line
                #time.sleep(0.5)
                #brake()
                last_seen_cx = None # Reset after adjustment to force re-detection of line
                lost_line_counter = 0 # Reset
        
        # --- Prepare Combined Debug View ---
        thresh_line_bgr = cv2.cvtColor(thresh_line, cv2.COLOR_GRAY2BGR)
        mask_green_bgr = cv2.cvtColor(mask_green, cv2.COLOR_GRAY2BGR)
        thresh_line_bgr_resized = cv2.resize(thresh_line_bgr, (thresh_line_bgr.shape[1], frame_resized.shape[0]))
        mask_green_bgr_resized = cv2.resize(mask_green_bgr, (mask_green_bgr.shape[1], frame_resized.shape[0]))
        # Add text overlays to the main debug display frame
        cv2.putText(debug_display_frame, f"Tindakan: {current_action_text}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(debug_display_frame, f"Garisan Dikesan: {line_detected_current_frame}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(debug_display_frame, f"Last Seen CX: {last_seen_cx if last_seen_cx is not None else 'N/A'}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(debug_display_frame, f"Kaunter Hilang: {lost_line_counter}/{LOST_LINE_THRESHOLD_FRAMES}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw ROI box on the main debug_display_frame (Blue)
        cv2.rectangle(debug_display_frame, (0, roi_start_y), (frame_resized.shape[1] - 1, roi_end_y - 1), (255, 0, 0), 2)
        cv2.putText(debug_display_frame, "ROI", (5, roi_start_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        mask_silver_bgr_resized = cv2.resize(mask_silver_bgr, (mask_silver_bgr.shape[1], frame_resized.shape[0]))
        combined_debug_view = np.hstack((debug_display_frame, thresh_line_bgr_resized, mask_green_bgr_resized, mask_silver_bgr_resized))
        cv2.imshow("Paparan Debug Kawalan Robot", combined_debug_view)
        
        # Tambahan: Throttling paparan untuk mengelakkan lag
        time.sleep(0.01)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Paparan debug ditutup oleh pengguna.")
            log_event("Navigasi Garisan debug window closed.")
            break
    cap_down.release()
    cv2.destroyAllWindows()
    print("Line navigator process ended.")
    log_event("Line navigator process ended.")

# === Utility: Debug Window Wrapper ===
def show_debug_window(name, image):
    """
    Displays an image in a named window for debugging.
    Returns True if 'q' is pressed, False otherwise.
    """
    cv2.imshow(name, image)
    # Tambahan: Throttling paparan untuk mengelakkan lag
    time.sleep(0.01)
    return cv2.waitKey(1) & 0xFF == ord('q')

# === Process 2: Detect Victims (YOLO) and Rescue ===
def victim_rescuer(rescue_flag, exit_flag, terminate_flag):
    """
    Detects silver and black 'balls' (victims) using a YOLO model.
    Grips the ball and releases it in a designated green or red zone.
    Transitions to the exit zone process after handling victims or timeout.
    """
    print("Ã°Å¸Å¸Â  Victim rescuer process started")
    log_event("Victim rescuer process started")
    # Gunakan laluan kamera yang stabil
    cap_front = cv2.VideoCapture(CAMERA_PATH_FRONT)
    if not cap_front.isOpened():
        print(f"Ã¢ÂÅ’ Kamera depan gagal dibuka dari {CAMERA_PATH_FRONT}.")
        log_event(f"Error: Front camera failed to open from {CAMERA_PATH_FRONT}.")
        return
    try:
        # Load YOLOv8 model
        model = YOLO("/home/pi/Desktop/competition/best.pt")
    except Exception as e:
        print(f"Ã¢ÂÅ’ Gagal memuat model YOLO: {e}")
        log_event(f"Error: Failed to load YOLO model: {e}")
        cap_front.release()
        return
    
    time.sleep(2) # Allow camera and model to initialize
    # Timeout for victim detection to prevent stalling
    detection_timeout = 15 # seconds
    last_active_time = time.time()
    current_action = "Menunggu (Zon Perak)"
    while True:
        if terminate_flag.value: # Check for termination signal
            print(f"{current_process().name}: Menerima isyarat penamatan. Menutup...")
            log_event(f"{current_process().name}: Received termination signal. Shutting down gracefully.")
            break # Exit the loop gracefully
        if not rescue_flag.value:
            last_active_time = time.time() # Reset timeout when not in rescue mode
            current_action = "Tidak Aktif"
            # Update debug view even when inactive
            ret, frame = cap_front.read()
            if ret:
                frame_display = frame.copy()
                cv2.putText(frame_display, f"Status: TIDAK AKTIF", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                cv2.putText(frame_display, f"Rescue: {rescue_flag.value}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame_display, f"Exit: {exit_flag.value}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame_display, f"Tindakan: {current_action}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                cv2.imshow("Pengesan Mangsa (Kamera Depan)", frame_display)
                
                # Tambahan: Throttling paparan untuk mengelakkan lag
                time.sleep(0.01)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Pengesan Mangsa debug window closed by user.")
                    log_event("Pengesan Mangsa debug window closed.")
                    break # Exit loop if debug window is closed
            time.sleep(0.1) # Small delay to prevent busy-waiting
            continue
        ret, frame = cap_front.read()
        if not ret:
            print("Ã¢ÂÅ’ Kamera depan gagal membaca frame.")
            log_event("Error: Front camera failed to read frame.")
            break
        # Perform YOLOv8 inference
        results = model(frame)[0] # Get the first result object
        frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Check for green and red zones for ball release
        green_zone_detected = cv2.countNonZero(cv2.inRange(frame_hsv, *HSV_THRESHOLDS["green_zone"])) > 1000
        red_mask1 = cv2.inRange(frame_hsv, *HSV_THRESHOLDS["red1"])
        red_mask2 = cv2.inRange(frame_hsv, *HSV_THRESHOLDS["red2"])
        red_zone_detected = cv2.countNonZero(red_mask1 + red_mask2) > 1000
        victim_handled = False
        num_silver_balls = 0
        num_black_balls = 0
        detected_ball_info = [] # Store (cx, cy, label) for all detected balls
        # Iterate through YOLOv8 detections
        for box in results.boxes:
            cls = int(box.cls[0])
            label = model.names[cls] # Get class name from model.names
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            if conf > 0.6: # Confidence threshold
                cx_ball = (x1 + x2) // 2
                cy_ball = (y1 + y2) // 2
                detected_ball_info.append((cx_ball, cy_ball, label, x1, y1, x2, y2)) # Store full box info too
                # Draw bounding box + label for all detected objects with conf > 0.6
                color = (0, 255, 0) if label == "silver_ball" else (0, 0, 255) # Green for silver, Red for black
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{label} ({conf:.2f})", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        # --- Movement Logic: Follow the Ball ---
        # Define the horizontal line for gripping
        grip_line_y = int(frame.shape[0] * 0.8) # 80% down the frame
        # --- NEW: Define the vertical center line for following ---
        center_line_x = frame.shape[1] // 2 # Center X of the camera frame
        tolerance_x = 30 # Pixels of tolerance for horizontal centering (can be adjusted)
        if detected_ball_info:
            # Prioritize a ball based on proximity (closest to bottom of frame)
            detected_ball_info.sort(key=lambda x: x[1], reverse=True) # Sort by cy (y-coordinate) descending
            
            target_cx, target_cy, target_label, _, _, _, _ = detected_ball_info[0] # Get info of the closest ball
            
            # Check if ball crosses the horizontal grip line
            if target_cy >= grip_line_y: # Ball has crossed or is on the grip line
                current_action = f"Bola Dekat ({target_label}): Bersedia untuk Genggam"
                brake() # Stop to prepare for gripping
                
                # Now check for zone and grip/release
                if target_label == "silver_ball":
                    num_silver_balls += 1 # Increment count when handling
                    if green_zone_detected:
                        current_action = "Melepaskan Bola Perak (Zon Hijau)"
                        print("Green zone found Ã¢â€ â€™ Releasing silver ball")
                        log_event("Released silver ball in green zone.")
                        release_ball()
                        victim_handled = True
                    else:
                        current_action = "Mencari Zon Hijau untuk Bola Perak"
                        # If not in zone, move slightly to find it
                        backward(50) # Small backward to adjust
                        time.sleep(0.2)
                        spin_right(80) # Spin to search for zone
                        time.sleep(0.5)
                        brake()
                elif target_label == "black_ball":
                    num_black_balls += 1 # Increment count when handling
                    if red_zone_detected:
                        current_action = "Melepaskan Bola Hitam (Zon Merah)"
                        print("Red zone found Ã¢â€ â€™ Releasing black ball")
                        log_event("Released black ball in red zone.")
                        release_ball()
                        victim_handled = True
                    else:
                        current_action = "Mencari Zon Merah untuk Bola Hitam"
                        # If not in zone, move slightly to find it
                        backward(50) # Small backward to adjust
                        time.sleep(0.2)
                        spin_left(80) # Spin to search for zone
                        time.sleep(0.5)
                        brake()
            else: # Ball is detected but has NOT crossed the grip line, so move towards it AND align horizontally
                # Align horizontally with the new center_line_x
                if target_cx < center_line_x - tolerance_x:
                    current_action = f"Mengikuti Bola ({target_label}): Belok Kiri"
                    left(300) # Adjust speed as needed
                    #time.sleep(0.1) # Added small delay
                elif target_cx > center_line_x + tolerance_x:
                    current_action = f"Mengikuti Bola ({target_label}): Belok Kanan"
                    right(300) # Adjust speed as needed
                    #time.sleep(0.1) # Added small delay
                else:
                    current_action = f"Mengikuti Bola ({target_label}): Maju"
                    backward(300) # Robot moves physically forward to approach the ball (camera is at the back, facing forward)
                    #time.sleep(0.1) # Added small delay
        else: # No balls detected, search pattern
            current_action = "Mencari Mangsa..."
            spin_right(80) # Spin slowly to search for balls
            time.sleep(0.1) # Added small delay
            # Or forward(50) for slow forward search
            
        # If a victim was handled, reset timeout and prepare to exit rescue mode
        if victim_handled:
            last_active_time = time.time() # Reset timeout
            print("Ã¢Å“â€¦ Victim handled. Continuing search or proceeding to exit zone.")
            current_action = "Mangsa Dikendalikan"
            # For now, we assume one victim then exit rescue mode
            rescue_flag.value = False # Deactivate victim rescue mode
            exit_flag.value = True    # Activate exit zone mode
            # No break here, allow the loop to re-evaluate flags next iteration
            # This allows the debug view to update before the process potentially exits.
            
        # --- Debug View ---
        frame_display = frame.copy() # Use the frame with YOLO overlays for display
        
        # --- Draw the horizontal grip line ---
        cv2.line(frame_display, (0, grip_line_y), (frame_display.shape[1], grip_line_y), (255, 0, 255), 2) # Magenta line
        cv2.putText(frame_display, f"Grip Line Y: {grip_line_y}", (10, grip_line_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
        # --- NEW: Draw the vertical center line ---
        cv2.line(frame_display, (center_line_x, 0), (center_line_x, frame_display.shape[0]), (0, 255, 255), 2) # Cyan line
        cv2.putText(frame_display, f"Center Line X: {center_line_x}", (center_line_x + 5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        # Indicate detected zones on debug view
        if green_zone_detected:
            cv2.putText(frame_display, "Zon Hijau Dikesan", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        if red_zone_detected:
            cv2.putText(frame_display, "Zon Merah Dikesan", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        # Tambah teks status pada paparan debug
        cv2.putText(frame_display, f"Status: {('AKTIF' if rescue_flag.value else 'TIDAK AKTIF')}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if rescue_flag.value else (0, 0, 255), 2)
        cv2.putText(frame_display, f"Bola Perak Dikesan: {num_silver_balls}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame_display, f"Bola Hitam Dikesan: {num_black_balls}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame_display, f"Tindakan: {current_action}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(frame_display, f"Rescue Flag: {rescue_flag.value}", (frame_display.shape[1] - 150, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame_display, f"Exit Flag: {exit_flag.value}", (frame_display.shape[1] - 150, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        if show_debug_window("Pengesan Mangsa (Kamera Depan)", frame_display):
            print("Pengesan Mangsa debug window closed by user.")
            log_event("Pengesan Mangsa debug window closed.")
            break
    cap_front.release()
    cv2.destroyAllWindows()
    print("Victim rescuer process ended.")
    log_event("Victim rescuer process ended.")

# === Process 3: Exit Zone and Resume ===
def zone_exiter(exit_flag, active_flag, terminate_flag):
    """
    Manages the robot's exit from the rescue zone.
    It looks for the black line to resume normal navigation or a red line to stop.
    """
    # Gunakan laluan kamera yang stabil
    cap_down = cv2.VideoCapture(CAMERA_PATH_DOWN) # Kamera bawah juga mungkin berubah indeks
    if not cap_down.isOpened():
        print(f"Ã¢ÂÅ’ Kamera bawah gagal dibuka untuk zone exiter dari {CAMERA_PATH_DOWN}.")
        log_event(f"Error: Downward camera failed to open for zone exiter from {CAMERA_PATH_DOWN}.")
        return
    time.sleep(2) # Allow camera to warm up
    current_action = "Mencari Garisan Keluar"
    while True:
        if terminate_flag.value: # Check for termination signal
            print(f"{current_process().name}: Menerima isyarat penamatan. Menutup...")
            log_event(f"{current_process().name}: Received termination signal. Shutting down gracefully.")
            break # Exit the loop gracefully
        if not exit_flag.value:
            current_action = "Tidak Aktif"
            # Update debug view even when inactive
            ret, frame = cap_down.read()
            if ret:
                frame_resized = cv2.resize(frame, (320, 240))
                roi_display = frame_resized[20:240, :].copy()
                cv2.putText(roi_display, f"Status: TIDAK AKTIF", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                cv2.putText(roi_display, f"Exit: {exit_flag.value}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(roi_display, f"Active: {active_flag.value}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(roi_display, f"Tindakan: {current_action}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                cv2.imshow("Keluar Zon (Kamera Bawah)", roi_display)
                
                # Tambahan: Throttling paparan untuk mengelakkan lag
                time.sleep(0.01)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Keluar Zon debug window closed by user.")
                    log_event("Keluar Zon debug window closed.")
                    break # Exit loop if debug window is closed
            time.sleep(0.1) # Small delay to prevent busy-waiting
            continue
        ret, frame = cap_down.read()
        if not ret:
            print("Ã¢ÂÅ’ Kamera bawah gagal membaca frame di zone exiter.")
            log_event("Error: Downward camera failed to read frame in zone exiter.")
            break
        frame_resized = cv2.resize(frame, (320, 240))
        roi = frame_resized[20:240, :] # Region of Interest
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        # --- Black Line Re-detection ---
        lower_black, upper_black = HSV_THRESHOLDS["black"] # Using general black threshold
        mask_black = cv2.inRange(hsv, lower_black, upper_black)
        if cv2.countNonZero(mask_black) > 500: # Threshold for black line presence
            forward(180) # Move forward to fully clear the silver zone
            current_action = "Garisan Hitam Dikesan Ã¢â€ â€™ Sambung Navigasi"
            print("Ã¢Â¬â€º Found black line again Ã¢â€ â€™ Resuming navigation")
            log_event("Black line re-detected. Resuming navigation.")
            active_flag.value = True # Reactivate line navigation
            exit_flag.value = False # Deactivate exit process
            break # Exit zone exiter loop
        # --- Red Line Detection (End of Mission) ---
        lower_red1, upper_red1 = HSV_THRESHOLDS["red1"]
        lower_red2, upper_red2 = HSV_THRESHOLDS["red2"]
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red2)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = mask_red1 + mask_red2
        if cv2.countNonZero(mask_red) > 500: # Threshold for red line presence
            current_action = "Garisan Merah Dikesan Ã¢â€ â€™ BERHENTI"
            print("Ã°Å¸â€Â´ Red line found Ã¢â€ â€™ STOPPING ALL OPERATIONS")
            log_event("Red line detected. Stopping all operations.")
            brake()
            active_flag.value = False # Stop line navigation
            exit_flag.value = False # Stop exit process
            break # Exit zone exiter loop
        
        # If neither black nor red line is found, keep moving or searching
        current_action = "Maju Perlahan (Mencari Garisan)"
        forward(100) # Keep moving slowly to find the line
        # --- Debug View ---
        # Buat salinan ROI untuk overlay teks
        roi_display = roi.copy()
        
        # Tambah teks status pada paparan debug
        cv2.putText(roi_display, f"Status: AKTIF", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(roi_display, f"Tindakan: {current_action}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(roi_display, f"Exit Flag: {exit_flag.value}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(roi_display, f"Active Flag: {active_flag.value}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        # Buat mask_black dan mask_red dalam format BGR untuk paparan
        mask_black_bgr = cv2.cvtColor(mask_black, cv2.COLOR_GRAY2BGR)
        mask_red_bgr = cv2.cvtColor(mask_red, cv2.COLOR_GRAY2BGR)
        # Tambah label pada mask
        cv2.putText(mask_black_bgr, "Mask Garisan Hitam", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(mask_red_bgr, "Mask Garisan Merah", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        # Gabungkan paparan
        debug_combined = np.hstack((roi_display, mask_black_bgr, mask_red_bgr))
        cv2.imshow("Keluar Zon (Kamera Bawah)", debug_combined)

        # Tambahan: Throttling paparan untuk mengelakkan lag
        time.sleep(0.01)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Keluar Zon debug window closed by user.")
            log_event("Keluar Zon debug window closed.")
            break
    cap_down.release()
    cv2.destroyAllWindows()
    print("Zone exiter process ended.")
    log_event("Zone exiter process ended.")

# === MAIN Execution Block ===
if __name__ == "__main__":
    # Shared flags for inter-process communication
    active_flag = Value('b', True)  # True: Line navigation active, False: Paused
    rescue_flag = Value('b', False) # True: Victim rescue active, False: Inactive
    exit_flag = Value('b', False)   # True: Exiting rescue zone, False: Inactive
    terminate_flag = Value('b', False) # New: Flag for graceful termination
    print("Ã°Å¸Å¡â‚¬ Starting robot control system...")
    log_event("Robot control system started.")
    # Create and start processes
    p1 = Process(target=line_navigator, args=(active_flag, rescue_flag, exit_flag, terminate_flag))
    p2 = Process(target=victim_rescuer, args=(rescue_flag, exit_flag, terminate_flag))
    p3 = Process(target=zone_exiter, args=(exit_flag, active_flag, terminate_flag))
    p1.start()
    p2.start()
    p3.start()
    try:
        # Wait for all processes to complete
        p1.join()
        p2.join()
        p3.join()
        print("Ã¢Å“â€¦ Semua proses telah selesai.")
        log_event("All processes completed successfully.")
    except KeyboardInterrupt:
        print("Ã°Å¸â€Â´ Dihentikan oleh pengguna. Menghentikan semua proses secara berhemah.")
        log_event("Robot control system interrupted by user. Initiating graceful shutdown.")
        terminate_flag.value = True # Signal processes to terminate gracefully
        # Give some time for processes to clean up before joining with timeout
        p1.join(timeout=5)
        p2.join(timeout=5)
        p3.join(timeout=5)
        # If any process is still alive after timeout, forcefully terminate
        if p1.is_alive(): p1.terminate()
        if p2.is_alive(): p2.terminate()
        if p3.is_alive(): p3.terminate()
        brake() # Ensure motors are stopped
    finally:
        print("Robot control system shut down.")
        log_event("Robot control system shut down.")
