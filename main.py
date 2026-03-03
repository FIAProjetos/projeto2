import cv2
import mediapipe as mp
import numpy as np
import serial
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

arduino = serial.Serial('COM1', 9600, timeout=1)
time.sleep(2)

base_options = python.BaseOptions(
    model_asset_path='pose_landmarker_lite.task'
)

options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO
)

pose = vision.PoseLandmarker.create_from_options(options)

contador = 0
fase = None

cap = cv2.VideoCapture(0)
timestamp = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (500, 500))
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgbA
    )

    timestamp += 33
    result = pose.detect_for_video(mp_image, timestamp)

    if result.pose_landmarks:
        landmarks = result.pose_landmarks[0]
        h, w, _ = frame.shape

        ombro = np.array([landmarks[12].x * w, landmarks[12].y * h])
        cotovelo = np.array([landmarks[14].x * w, landmarks[14].y * h])
        punho = np.array([landmarks[16].x * w, landmarks[16].y * h])

        angulo = np.degrees(
            np.arctan2(punho[1] - cotovelo[1], punho[0] - cotovelo[0]) -
            np.arctan2(ombro[1] - cotovelo[1], ombro[0] - cotovelo[0])
        )

        angulo = abs(angulo)
        if angulo > 180:
            angulo = 360 - angulo

        if angulo > 160:
            fase = 'descendo'

        if angulo < 40 and fase == 'descendo':
            fase = 'subindo'
            contador += 1

        if contador == 12:
            arduino.write(b'1\n')
            contador = 0

        for lm in [12, 14, 16]:
            cx = int(landmarks[lm].x * w)
            cy = int(landmarks[lm].y * h)
            cv2.circle(frame, (cx, cy), 6, (0, 255, 0), -1)

        cv2.putText(frame, f"Angulo: {int(angulo)}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (255, 255, 0), 2)

        cv2.putText(frame, f"Repeticoes: {contador}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0), 2)

    cv2.imshow("Rosca Biceps - LED a cada 12 reps", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
arduino.close()
