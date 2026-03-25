import cv2
import json
import os

MODEL_PATH = "models/trainer.yml"
LABELS_PATH = "models/labels.json"

if not os.path.exists(MODEL_PATH) or not os.path.exists(LABELS_PATH):
    raise RuntimeError("Model files not found. Run train_lbph.py first.")

if not hasattr(cv2, "face"):
    raise RuntimeError("cv2.face module not found. Install opencv-contrib-python.")

with open(LABELS_PATH, "r") as f:
    label_map = json.load(f)

# json keys are strings, convert to int lookup
label_map = {int(k): v for k, v in label_map.items()}

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(MODEL_PATH)

face_cascade = cv2.CascadeClassifier(
    "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"
)

PROFILES_PATH = "profiles.json"

if not os.path.exists(PROFILES_PATH):
    raise RuntimeError("profiles.json not found. Run manage_profiles.py first.")

with open(PROFILES_PATH, "r") as f:
    PROFILES = json.load(f)

if "Unknown" not in PROFILES:
    PROFILES["Unknown"] = {
        "risk": "Unknown",
        "style": "Cautious",
        "robot_response": "Do not personalise yet"
    }

# Lower confidence is better for LBPH
# Try 60-85 depending on your camera and lighting
CONFIDENCE_THRESHOLD = 70

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("[INFO] Live face recognition started.")
print("[INFO] Press q to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Failed to read from camera.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(80, 80)
    )

    if len(faces) == 0:
        print("Detected user: None")
    else:
        for (x, y, w, h) in faces:
            face_crop = gray[y:y+h, x:x+w]
            face_crop = cv2.resize(face_crop, (200, 200))

            label_id, confidence = recognizer.predict(face_crop)

            if confidence < CONFIDENCE_THRESHOLD:
                name = label_map.get(label_id, "Unknown")
            else:
                name = "Unknown"

            profile = PROFILES.get(name, PROFILES["Unknown"])

            text1 = f"User: {name}"
            text2 = f"Risk: {profile['risk']} | Style: {profile['style']}"
            text3 = f"Conf: {confidence:.1f}"

            print(f"Detected user: {name} | confidence={confidence:.1f} | risk={profile['risk']} | style={profile['style']}")

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, text1, (x, y - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, text2, (x, y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(frame, text3, (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

    cv2.imshow("Live Face Recognition", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("[DONE] Stopped.")
