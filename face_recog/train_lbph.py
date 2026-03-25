import cv2
import os
import json
import numpy as np

dataset_dir = "dataset"
model_dir = "models"
os.makedirs(model_dir, exist_ok=True)

if not hasattr(cv2, "face"):
    raise RuntimeError("cv2.face module not found. Install opencv-contrib-python.")

recognizer = cv2.face.LBPHFaceRecognizer_create()

faces = []
labels = []
label_map = {}
current_id = 0

for person_name in sorted(os.listdir(dataset_dir)):
    person_path = os.path.join(dataset_dir, person_name)
    if not os.path.isdir(person_path):
        continue

    label_map[current_id] = person_name

    for file_name in os.listdir(person_path):
        file_path = os.path.join(person_path, file_name)
        img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue

        faces.append(img)
        labels.append(current_id)

    current_id += 1

if len(faces) == 0:
    raise RuntimeError("No training images found inside dataset/")

labels = np.array(labels)
recognizer.train(faces, labels)

recognizer.save(os.path.join(model_dir, "trainer.yml"))

with open(os.path.join(model_dir, "labels.json"), "w") as f:
    json.dump(label_map, f, indent=2)

print("[DONE] Model trained and saved to models/")
print("[INFO] Labels:", label_map)
