import cv2
import mediapipe as mp
import numpy as np
import time

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - \
              np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)

    if angle > 180:
        angle = 360-angle

    return angle


def analyze_workout(exercise="curl"):
    cap = cv2.VideoCapture(0)

    counter = 0
    stage = None
    scores = []
    fatigue_score = 0
    rep_times = []

    with mp_pose.Pose(min_detection_confidence=0.5,
                      min_tracking_confidence=0.5) as pose:

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            try:
                landmarks = results.pose_landmarks.landmark

                # -------------------------
                # CURL
                # -------------------------
                if exercise == "curl":
                    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]

                    elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]

                    wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

                    angle = calculate_angle(shoulder, elbow, wrist)

                    if angle > 160:
                        stage = "down"

                    if angle < 40 and stage == "down":
                        stage = "up"
                        counter += 1
                        scores.append(angle)
                        rep_times.append(time.time())

                # -------------------------
                # SQUAT
                # -------------------------
                if exercise == "squat":
                    hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                           landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]

                    knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                            landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]

                    ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

                    angle = calculate_angle(hip, knee, ankle)

                    # Back posture detection
                    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]

                    back_angle = calculate_angle(shoulder, hip, knee)

                    if back_angle < 150:
                        cv2.putText(image, "KEEP BACK STRAIGHT",
                                    (50, 150),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.8, (0, 0, 255), 2)

                    if angle > 160:
                        stage = "up"

                    if angle < 90 and stage == "up":
                        stage = "down"
                        counter += 1
                        scores.append(angle)
                        rep_times.append(time.time())

                # -------------------------
                # PUSHUP
                # -------------------------
                if exercise == "pushup":
                    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]

                    elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]

                    wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

                    angle = calculate_angle(shoulder, elbow, wrist)

                    if angle > 160:
                        stage = "up"

                    if angle < 90 and stage == "up":
                        stage = "down"
                        counter += 1
                        scores.append(angle)
                        rep_times.append(time.time())

            except:
                pass

            # Fatigue detection
            if len(rep_times) > 3:
                last_three = rep_times[-3:]
                avg_time = (last_three[-1] - last_three[0]) / 2
                if avg_time > 3:
                    fatigue_score += 1

            # Rest suggestion
            if fatigue_score > 2:
                cv2.putText(image, "TAKE REST 10s",
                            (200, 200),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 0, 255), 3)

            cv2.rectangle(image, (0, 0), (250, 80), (245, 117, 16), -1)
            cv2.putText(image, f"Reps: {counter}",
                        (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1, (255, 255, 255), 2)

            mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS
            )

            cv2.imshow("Workout Tracker", image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    # ---- POST LOOP CALCULATIONS ----
    avg_score = 80 if not scores else min(95, max(60, sum(scores)/len(scores)))
    calories = counter * 0.6

    rep_speeds = []
    for i in range(1, len(rep_times)):
        rep_speeds.append(rep_times[i] - rep_times[i-1])

    avg_speed = sum(rep_speeds)/len(rep_speeds) if rep_speeds else 0

    feedback = []

    if avg_score < 70:
        feedback.append("Improve depth or control.")

    if fatigue_score > 2:
        feedback.append("Fatigue detected. Reduce pace.")

    if not feedback:
        feedback.append("Excellent performance!")

    return {
        "reps": counter,
        "avg_score": round(avg_score, 2),
        "calories": round(calories, 2),
        "feedback": feedback,
        "rep_speeds": rep_speeds,
        "avg_speed": round(avg_speed, 2)
    }