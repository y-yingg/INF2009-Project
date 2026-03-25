import cv2
import os
import sys

if len(sys.argv) < 2:
    print("Usage: python collect_faces.py <PersonName> [num_samples]")
    print("Example: python collect_faces.py Grandma 30")
    sys.exit(1)

person_name = sys.argv[1]
num_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 30

save_dir = os.path.join("dataset", person_name)
os.makedirs(save_dir, exist_ok=True)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

face_cascade = cv2.CascadeClassifier(
    "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"
)

count = 0
frame_skip = 0

print(f"[INFO] Collecting faces for: {person_name}")
print("[INFO] Look at the camera. Slightly change angle and expression.")
print("[INFO] Press q to quit early.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Could not read from camera.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(80, 80)
    )

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        frame_skip += 1
        if frame_skip % 5 == 0 and count < num_samples:
            face_crop = gray[y:y+h, x:x+w]
            face_crop = cv2.resize(face_crop, (200, 200))
            filename = os.path.join(save_dir, f"{count:03d}.jpg")
            cv2.imwrite(filename, face_crop)
            count += 1
            print(f"[INFO] Saved {filename}")

        break  # only save first detected face per frame

    cv2.putText(frame, f"{person_name}: {count}/{num_samples}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                (0, 255, 0), 2)

    cv2.imshow("Collect Faces", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q") or count >= num_samples:
        break

cap.release()
cv2.destroyAllWindows()
print("[DONE] Collection finished.")
