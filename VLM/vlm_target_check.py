import os
import cv2
import json
import time
import base64
from collections import deque
from openai import OpenAI

MODEL_PATH = "models/trainer.yml"
LABELS_PATH = "models/labels.json"
CASCADE_PATH = "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"
PROFILES_PATH = "profiles.json"

# Face recognition tuning
CONFIDENCE_THRESHOLD = 70          # lower is stricter for LBPH
STABLE_MATCH_TARGET = 3            # how many target matches needed
STABLE_WINDOW = 5                  # over last N recognised frames
FRAME_CAPTURE_COUNT = 3            # number of frames to send to VLM
FRAME_CAPTURE_GAP_SEC = 0.6        # gap between captured frames

# Vision model
OPENAI_MODEL = "gpt-4.1-mini"

def require_files():
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError("Missing models/trainer.yml. Run train_lbph.py first.")
    if not os.path.exists(LABELS_PATH):
        raise RuntimeError("Missing models/labels.json. Run train_lbph.py first.")
    if not os.path.exists(CASCADE_PATH):
        raise RuntimeError(f"Missing cascade file: {CASCADE_PATH}")
    if not os.path.exists(PROFILES_PATH):
        raise RuntimeError("profiles.json not found. Run manage_profiles.py first.")
    if not hasattr(cv2, "face"):
        raise RuntimeError("cv2.face not found. Your OpenCV install does not support LBPH.")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set in this terminal session.")


def load_profiles():
    with open(PROFILES_PATH, "r") as f:
        profiles = json.load(f)

    if "Unknown" not in profiles:
        profiles["Unknown"] = {
            "risk": "Unknown",
            "style": "Cautious",
            "robot_response": "Do not personalise yet"
        }

    return profiles



def load_face_system():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)

    with open(LABELS_PATH, "r") as f:
        label_map = json.load(f)
    label_map = {int(k): v for k, v in label_map.items()}

    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    if face_cascade.empty():
        raise RuntimeError("Failed to load Haar cascade.")

    return recognizer, label_map, face_cascade


def encode_image_to_data_url(frame):
    ok, buffer = cv2.imencode(".jpg", frame)
    if not ok:
        raise RuntimeError("Failed to encode frame as JPEG.")
    b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def parse_vlm_text(text):
    result = {
        "activity": "unclear",
        "distress": "unclear",
        "summary": text.strip(),
    }

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        lower = line.lower()
        if lower.startswith("activity:"):
            result["activity"] = line.split(":", 1)[1].strip()
        elif lower.startswith("distress:"):
            result["distress"] = line.split(":", 1)[1].strip()
        elif lower.startswith("summary:"):
            result["summary"] = line.split(":", 1)[1].strip()

    return result


def ask_vlm_about_target(target_name, frames):
    client = OpenAI()

    content = [
        {
            "type": "text",
            "text": (
                f"You are analysing a home scene. "
                f"The target person is '{target_name}'. "
                f"Focus on that target person only. "
                f"If multiple people appear, prioritise the target person. "
                f"Return exactly three lines in this format:\n"
                f"Activity: <short activity>\n"
                f"Distress: <yes/no/unclear>\n"
                f"Summary: <one concise sentence>\n\n"
                f"Allowed activities examples: studying, using phone, sitting, standing, lying down, walking, playing piano, eating, talking, unclear."
            ),
        }
    ]

    for frame in frames:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": encode_image_to_data_url(frame),
                    "detail": "low"
                }
            }
        )

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "developer",
                "content": "Be concise and follow the requested output format exactly."
            },
            {
                "role": "user",
                "content": content
            }
        ],
        temperature=0.2,
    )

    text = response.choices[0].message.content
    return parse_vlm_text(text)


def recognise_name_from_frame(frame, recognizer, label_map, face_cascade):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(80, 80)
    )

    detections = []

    for (x, y, w, h) in faces:
        face_crop = gray[y:y+h, x:x+w]
        face_crop = cv2.resize(face_crop, (200, 200))
        label_id, confidence = recognizer.predict(face_crop)

        if confidence < CONFIDENCE_THRESHOLD:
            name = label_map.get(label_id, "Unknown")
        else:
            name = "Unknown"

        detections.append({
            "name": name,
            "confidence": confidence,
            "bbox": (x, y, w, h),
        })

    return detections


def capture_target_frames(target_name, recognizer, label_map, face_cascade):
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        raise RuntimeError("Could not open camera.")

    recent_matches = deque(maxlen=STABLE_WINDOW)
    captured_frames = []

    print(f"\n[INFO] Looking for target: {target_name}")
    print("[INFO] Press q to cancel this search.")

    last_capture_time = 0
    target_locked = False

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to read frame from camera.")
                break

            detections = recognise_name_from_frame(frame, recognizer, label_map, face_cascade)

            found_target_this_frame = False

            for det in detections:
                x, y, w, h = det["bbox"]
                name = det["name"]
                conf = det["confidence"]

                if name == target_name:
                    found_target_this_frame = True
                    colour = (0, 255, 0)
                elif name == "Unknown":
                    colour = (0, 0, 255)
                else:
                    colour = (255, 255, 0)

                cv2.rectangle(frame, (x, y), (x+w, y+h), colour, 2)
                cv2.putText(
                    frame,
                    f"{name} ({conf:.1f})",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    colour,
                    2
                )

            recent_matches.append(found_target_this_frame)

            stable_count = sum(recent_matches)
            cv2.putText(
                frame,
                f"Target={target_name} Stable={stable_count}/{STABLE_WINDOW}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            if stable_count >= STABLE_MATCH_TARGET:
                target_locked = True

            if target_locked:
                now = time.time()
                if now - last_capture_time >= FRAME_CAPTURE_GAP_SEC:
                    captured_frames.append(frame.copy())
                    last_capture_time = now
                    print(f"[INFO] Captured frame {len(captured_frames)}/{FRAME_CAPTURE_COUNT}")

                if len(captured_frames) >= FRAME_CAPTURE_COUNT:
                    cv2.imshow("Target Search", frame)
                    cv2.waitKey(300)
                    return captured_frames

            cv2.imshow("Target Search", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print("[INFO] Search cancelled.")
                return []

    finally:
        cap.release()
        cv2.destroyAllWindows()


def choose_target_name(valid_names):
    print("\nAvailable names:")
    for i, name in enumerate(valid_names, start=1):
        print(f"  {i}. {name}")

    while True:
        raw = input("\nType target name or number: ").strip()

        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(valid_names):
                return valid_names[idx - 1]

        for name in valid_names:
            if raw.lower() == name.lower():
                return name

        print("Invalid choice. Try again.")

def main():
    require_files()
    profiles = load_profiles()
    recognizer, label_map, face_cascade = load_face_system()

    known_names = sorted(set(label_map.values()))
    known_names = [name for name in known_names if name != "Unknown"]

    print("[OK] Targeted VLM checker ready.")

    while True:
        target_name = choose_target_name(known_names)

        frames = capture_target_frames(target_name, recognizer, label_map, face_cascade)

        if not frames:
            again = input("\nNo frames analysed. Analyse another person? (y/n): ").strip().lower()
            if again != "y":
                break
            continue

        print("[INFO] Sending frames to VLM...")

        try:
            vlm_result = ask_vlm_about_target(target_name, frames)
        except Exception as e:
            print(f"[ERROR] VLM request failed: {e}")
            again = input("\nAnalyse another person? (y/n): ").strip().lower()
            if again != "y":
                break
            continue

        profile = profiles.get(target_name, profiles["Unknown"])

        print("\n===== RESULT =====")
        print(f"Target:   {target_name}")
        print(f"Risk:     {profile['risk']}")
        print(f"Style:    {profile['style']}")
        print(f"Response: {profile.get('robot_response', 'No response defined')}")
        print(f"Activity: {vlm_result['activity']}")
        print(f"Distress: {vlm_result['distress']}")
        print(f"Summary:  {vlm_result['summary']}")
        print("==================")

        again = input("\nAnalyse another person? (y/n): ").strip().lower()
        if again != "y":
            break

    print("[DONE] Exiting.")


if __name__ == "__main__":
    main()
