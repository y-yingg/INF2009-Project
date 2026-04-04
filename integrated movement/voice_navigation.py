#!/usr/bin/env python3
import sys
import os
import time
import numpy as np
import pyaudio
import rclpy
import cv2
import json

# Add path to action.py (adjust if needed)
sys.path.insert(0, '/home/ubuntu/ros2_ws/src/large_models/large_models')

from reliable_navigation import ReliableNavigator
from commands_nomqtt import CommandDetector
from action import PuppyControlNode

# ------------------ Face Recognition Setup ------------------
MODEL_PATH = "models/trainer.yml"
LABELS_PATH = "models/labels.json"
PROFILES_PATH = "profiles.json"
CASCADE_PATH = "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"
CONFIDENCE_THRESHOLD = 70

with open(LABELS_PATH, "r") as f:
    label_map = json.load(f)
label_map = {int(k): v for k, v in label_map.items()}

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(MODEL_PATH)

with open(PROFILES_PATH, "r") as f:
    PROFILES = json.load(f)
if "Unknown" not in PROFILES:
    PROFILES["Unknown"] = {"risk": "Unknown", "style": "Cautious", "robot_response": "Do not personalise yet"}

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

def detect_and_recognize(timeout=5):
    """Captures video and returns recognized user name or None."""
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    start_time = time.time()
    recognized_name = None

    print("Scanning for face...")
    while time.time() - start_time < timeout:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))

        for (x, y, w, h) in faces:
            face_crop = gray[y:y+h, x:x+w]
            face_crop = cv2.resize(face_crop, (200, 200))
            label_id, confidence = recognizer.predict(face_crop)

            if confidence < CONFIDENCE_THRESHOLD:
                name = label_map.get(label_id, "Unknown")
                if name != "Unknown":
                    recognized_name = name
                    break

        if recognized_name is not None:
            break

    cap.release()
    cv2.destroyAllWindows()
    return recognized_name

# ------------------ Main ------------------
def main():
    rclpy.init()

    # Create nodes only once
    navigator = ReliableNavigator()
    detector = CommandDetector(mqtt_client=None)
    puppy_ctrl = PuppyControlNode()          # Single instance reused

    TARGET_X = 1.0
    TARGET_Y = 1.0
    TARGET_THETA = 0.0

    # Audio capture setup
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 48000
    CHUNK = 4096

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Listening for wake words and commands...")
    print(f"Command will move robot to ({TARGET_X}, {TARGET_Y}), then sit, scan face, and bow/box.")

    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            detector.process_next(audio_data)

            intent = detector.get_last_intent()
            if intent:
                print(f"Command '{intent}' detected! Moving to ({TARGET_X}, {TARGET_Y})...")

                success = navigator.send_goal(TARGET_X, TARGET_Y, TARGET_THETA)

                if success:
                    print("Robot arrived at destination.")

                    # Sit
                    puppy_ctrl.sit()
                    print("Sit command sent.")
                    # Allow time for action to execute
                    for _ in range(10):
                        rclpy.spin_once(puppy_ctrl, timeout_sec=0.1)
                        time.sleep(0.1)

                    # Face recognition
                    recognized = detect_and_recognize(timeout=5)

                    if recognized:
                        print(f"Recognized user: {recognized}. Performing bow...")
                        puppy_ctrl.bow()
                    else:
                        print("No known face detected. Robot boxing.")
                        puppy_ctrl.boxing()

                    # Allow time for action to be sent
                    for _ in range(10):
                        rclpy.spin_once(puppy_ctrl, timeout_sec=0.1)
                        time.sleep(0.1)

                else:
                    print("Failed to reach destination.")

                time.sleep(1)  # brief pause before next command

    except KeyboardInterrupt:
        print("\nShutting down...")

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        puppy_ctrl.destroy_node()
        navigator.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
