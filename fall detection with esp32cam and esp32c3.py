import cv2
import mediapipe as mp
import math
import time
import requests

# ESP32-CAM Stream URL
url = "http://192.168.43.144:81/stream"

# XIAO ESP32-C3 IP Address
ESP32_IP = "192.168.43.53"

cap = cv2.VideoCapture(url)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

mp_draw = mp.solutions.drawing_utils

fall_detected = False
fall_time = 0
buzzer_on = False


def calculate_body_angle(shoulder, hip):
    x1, y1 = shoulder
    x2, y2 = hip

    angle = abs(math.degrees(math.atan2(y2 - y1, x2 - x1)))
    return angle


# Create larger resizable window
cv2.namedWindow("ESP32-CAM Fall Detection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("ESP32-CAM Fall Detection", 800, 600)

while True:

    success, frame = cap.read()

    if not success:
        print("Failed to receive frame")
        break

    # Fix camera orientation
    frame = cv2.rotate(frame, cv2.ROTATE_180)
    frame = cv2.flip(frame, 1)

    # Increase video size
    frame = cv2.resize(frame, (1280, 720))

    h, w, c = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = pose.process(rgb)

    if results.pose_landmarks:

        landmarks = results.pose_landmarks.landmark

        # Right Shoulder
        shoulder = (
            int(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x * w),
            int(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y * h)
        )

        # Right Hip
        hip = (
            int(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x * w),
            int(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y * h)
        )

        # Draw skeleton
        mp_draw.draw_landmarks(
            frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )

        # Draw body line
        cv2.line(frame, shoulder, hip, (0, 255, 0), 3)

        # Calculate angle
        angle = calculate_body_angle(shoulder, hip)

        cv2.putText(
            frame,
            f"Angle: {int(angle)}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )

        # FALL DETECTION
        if angle < 45 or angle > 135:

            if not fall_detected:
                fall_detected = True
                fall_time = time.time()

            elapsed = time.time() - fall_time

            # Fall detected text at bottom
            cv2.putText(
                frame,
                "FALL DETECTED",
                (20, h - 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (0, 0, 255),
                4
            )

            # Timer at bottom
            cv2.putText(
                frame,
                f"Time: {elapsed:.1f}s",
                (20, h - 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2
            )

            # Turn ON buzzer after 2 seconds
            if elapsed >= 5 and not buzzer_on:

                try:
                    response = requests.get(
                        f"http://{ESP32_IP}/lighton",
                        timeout=1
                    )

                    print("Buzzer ON:", response.text)
                    buzzer_on = True

                except Exception as e:
                    print("ESP32 Error:", e)

        else:

            fall_detected = False

            # Turn OFF buzzer
            if buzzer_on:

                try:
                    response = requests.get(
                        f"http://{ESP32_IP}/lightoff",
                        timeout=1
                    )

                    print("Buzzer OFF:", response.text)
                    buzzer_on = False

                except Exception as e:
                    print("ESP32 Error:", e)

    cv2.imshow("ESP32-CAM Fall Detection", frame)

    key = cv2.waitKey(1)

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
