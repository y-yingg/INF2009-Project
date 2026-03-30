# Face Recognition Module (Diary / Development Log)

## 1. Overview
This module implements a lightweight face recognition pipeline designed to run on edge devices (Raspberry Pi).  
The goal is to identify users locally and link them to personalised profiles (e.g. risk level, response style).

The pipeline consists of:
- Face data collection
- Model training (LBPH)
- Real-time face recognition
- Profile mapping for personalised behaviour

---

## 2. Implementation Details

### 2.1 Face Data Collection
We implemented a data collection script to capture face samples from the camera.

- Script: `collect_faces.py`
- Captures grayscale face images
- Resizes to 200x200 for consistency
- Saves images into dataset folders per user

**Key design decisions:**
- Frame skipping (every 5 frames) to reduce redundant samples
- Minimum face size filtering to improve detection quality
- Manual variation (angle, expression) encouraged for robustness

**Challenges:**
- Lighting conditions significantly affected detection consistency
- Needed to balance sample quantity vs data redundancy

---

### 2.2 Model Training
We used the LBPH (Local Binary Patterns Histogram) algorithm for face recognition.

- Script: `train_lbph.py`

**Reasons for choosing LBPH:**
- Lightweight and suitable for edge devices
- Does not require GPU
- Performs well for small datasets (household-scale users)

**Process:**
- Load images from dataset folder
- Assign labels per user
- Train LBPH recognizer
- Save trained model (`trainer.yml`) and label mapping (`labels.json`)

---

### 2.3 Real-Time Recognition
We implemented a live recognition system using webcam input.

- Script: `recognize_live.py`

**Pipeline:**
1. Capture frame from camera  
2. Detect faces using Haar Cascade  
3. Convert to grayscale and resize  
4. Predict using LBPH model  
5. Compare confidence threshold  
6. Display user label + profile info  

**Key design:**
- Confidence threshold = 70 (tuned experimentally)
- Lower confidence = better match (LBPH-specific)

If confidence is too high → classify as **Unknown**

---

### 2.4 Profile Mapping
We linked recognised users to behaviour profiles.

- Script: `manage_profiles.py`
- Data: `profiles.json`

Each user has:
- Risk level (High / Medium / Low)
- Interaction style (Gentle / Playful / Normal)
- Robot response strategy

**Example:**
- Grandma → High risk → escalate quickly  
- Child → Low risk → observe first  

This enables → **personalised downstream decision-making**

---

## 3. Optimisation & Edge Considerations

### 3.1 Model Choice
We intentionally avoided heavy models (e.g. deep CNNs):
- LBPH chosen for low CPU usage
- Works offline (no cloud dependency)

### 3.2 Image Preprocessing
- Converted to grayscale → reduces computation
- Resized to fixed resolution (200x200)
- Reduced input variability

### 3.3 Frame Skipping
During data collection:
- Only saved every 5 frames
- Reduces dataset redundancy
- Improves training efficiency

### 3.4 Threshold Tuning
- Tested confidence thresholds between 60–85
- Selected 70 as balance between:
  - False positives (wrong identity)
  - False negatives (Unknown)

---

## 4. Testing & Observations

### Successful Cases
- Correct identification for trained users under normal lighting
- Stable recognition when face is frontal

### Limitations
- Performance drops under:
  - Low lighting
  - Extreme angles
  - Partial occlusion

- Requires retraining when adding new users
- Limited scalability (not suitable for large user sets)

---

## 5. Integration Status

**Current state:**
- Face recognition module works independently
- Profile mapping is functional

**Limitations:**
- Not fully integrated with all system modules (e.g. navigation, VLM)
- Real-time multi-module execution may cause performance overhead

---

## 6. Future Improvements

- Improve robustness under varying lighting conditions
- Explore lightweight deep learning alternatives
- Enable incremental learning (avoid full retraining)
- Further optimise runtime performance for multi-module execution

---

## 7. Setup Instructions

```bash
bash setup.sh
```

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 8. Summary

This module demonstrates:
- Local face recognition on edge device
- User-specific profile mapping
- Foundation for personalised, context-aware system

Although not fully integrated, it successfully shows how identity can be used to influence system behaviour.
