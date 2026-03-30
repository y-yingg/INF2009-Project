# Vision Language Model (VLM) Module (Diary / Development Log)

## 1. Overview
This module implements scene understanding using a Vision Language Model (VLM) to interpret visual context beyond basic detection.

The goal is to:
- Understand what is happening in the scene
- Detect potential distress situations
- Provide contextual information to support decision-making

This complements face recognition by answering:
→ not just *who*, but also *what is happening*

---

## 2. Initial Approach (Cloud-based VLM)

### 2.1 API-based Implementation
Initially, we implemented VLM using a cloud-based API.

Scripts:
- `vlm_scene_check.py`
- `vlm_question_check.py`
- `vlm_target_check.py`

Features:
- Scene description (activity, distress, summary)
- Question answering (e.g. “Is the person reading?”)
- Target-specific analysis using face recognition + VLM

Pipeline:
1. Capture image from camera
2. Encode image to base64
3. Send to API
4. Receive text response
5. Parse structured output

---

### 2.2 Limitations Identified
During testing, several issues were observed:

- Requires internet connection
- Introduces latency due to API calls
- Not suitable for real-time edge deployment
- Raises privacy concerns (image sent to cloud)

This contradicts the project goal of:
→ **edge-based, low-latency, privacy-preserving system**

---

## 3. Optimisation: Migration to Offline VLM

### 3.1 Design Change
To address the above limitations, we redesigned the VLM module to run locally.

We switched to:
- Local model: **SmolVLM-500M-Instruct**
- Script: `offline_vlm_question.py`

This represents a key optimisation step:
→ moving from **cloud dependency → edge-based inference**

---

### 3.2 Offline VLM Implementation

Key components:
- HuggingFace Transformers (local loading)
- PyTorch inference
- On-device image processing

Pipeline:
1. Capture frame from camera
2. Convert image to RGB
3. Pass image + prompt to local VLM
4. Generate response directly on device

Key design:
- `local_files_only=True` ensures no internet usage
- Device-aware loading (CPU / GPU)
- Reduced token generation for efficiency

---

### 3.3 Preset Task Optimisation
To improve usability and consistency, preset task templates were added.

Script:
- `offline_vlm_preset_check.py`

Examples:
- Check if studying
- Check if using phone
- Check if in distress
- Activity ranking

Benefits:
- Standardised output format
- Reduced ambiguity in responses
- Faster interaction for testing

---

## 4. Edge Optimisation Considerations

### 4.1 Model Selection
We selected a small VLM model (500M parameters):
- Fits within edge constraints
- Lower memory usage
- Faster inference compared to larger models

### 4.2 Local Inference
- No API calls → reduced latency
- No data transmission → improved privacy
- Works offline → more robust deployment

### 4.3 Prompt Design
- Structured prompts used to control output format
- Ensures predictable and parsable results

---

## 5. Testing & Observations

### Successful Cases
- Able to generate scene descriptions (activity + summary)
- Can answer targeted questions about scene
- Detects simple activities (e.g. sitting, using phone)

### Limitations
- Lower accuracy compared to large cloud models
- Slower inference on CPU-only devices
- May produce vague or “unclear” outputs

---

## 6. Integration Status

Current state:
- Offline VLM works independently
- Integrated conceptually with face recognition

Limitations:
- Not fully integrated into full pipeline (MQTT / actions)
- Sequential execution may affect performance

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
- Scene understanding using VLM
- Transition from cloud-based to edge-based AI
- Trade-off between accuracy and efficiency

Most importantly, it shows:
→ **how AI models can be adapted to meet edge computing constraints**

This optimisation aligns with the core goal of the project:
→ enabling context-aware intelligence directly on-device.
