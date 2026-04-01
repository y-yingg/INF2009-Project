# Context-Aware Edge AI System (Project Diary)

## 1. Overview
This project implements a **context-aware robotic system** that combines:
- Face Recognition (identity)
- Audio Detection (Commands)
- Vision Language Model (scene understanding)
- MQTT Backbone (communication)
- Alerting + Cloud Logging

The goal is to move beyond simple rule-based systems by enabling:
→ **personalised and context-aware decision-making on edge devices**

---

## 2. System Architecture

The system consists of 3 main subsystems:

### 2.1 Perception Layer
- Face Recognition → identifies user
- VLM → understands scene context
- Audio Detection → captures voice commands

### 2.2 Communication Layer
- MQTT backbone (publish / subscribe)
- Standardised topics (user, scene, severity, etc.)

### 2.3 Action Layer
- Telegram alerts
- Dashboard monitoring
- Cloud logging (Google Sheets)

---

## 3. Development Approach (Key Iteration)

### Initial Design (Planned)
- Fully integrated system
- Multiple modules running together in real time
- Cloud + edge hybrid approach

### Actual Implementation
Due to system complexity and edge constraints:
- Modules were first developed **independently**
- Integration was done partially
- Focus shifted to demonstrating **core concepts**

Most importantly:
→ We iteratively improved design to better fit **edge computing constraints**

---

## 4. Face Recognition Module

(Refer to `face_recog/README.md` for full diary)

### Key Features
- Local face recognition using LBPH
- User profile mapping (risk, style, response)
- Unknown detection for untrained faces

### Edge Optimisation
- Lightweight algorithm (LBPH instead of deep models)
- Grayscale + resizing to reduce computation
- Threshold tuning for balance between accuracy and reliability

### Key Insight
Face recognition provides:
→ **“who the user is”**, enabling personalised behaviour

---
---

## 5. Audio Detection Module
(Refer to `inf2009_project_audio_detection/README.md` for full diary)

### Key Features
- Wake-word detection by recognizing trigger phrases
- Command parsing through intent extraction
- Speaker identification through voice analysis

### Edge Optimisation
- High latency using lightweight models without GPU acceleration
- Audio privacy with no raw audio leaving device unless authorized
- Resource constraints through resampled audio to 16kHz mono, processing in small buffers and releasing memory after inference
- Background noise by implementing a simple Voice Activity Detection (VAD) to filter silence before feeding into the model

### Key Insight
- Moves interaction from button-based to natural voice
- Processing on edge provides low latency and preserve user privacy

---

## 6. VLM Module (Major Optimisation Highlight)

(Refer to `vlm/README.md` for full diary)

### Initial Approach (Cloud-based)
- Used API-based VLM for:
  - Scene description
  - Question answering
- Worked well but had issues:
  - Internet dependency
  - High latency
  - Privacy concerns

### Optimisation (Key Improvement)
We redesigned the module to run locally:
- Switched to **offline VLM (SmolVLM-500M)**
- Removed API dependency completely

### Impact
- Reduced latency
- Improved privacy (no image upload)
- Fully aligned with edge computing goals

### Trade-off
- Slightly lower accuracy compared to cloud models

### Key Insight
This represents:
→ **architectural optimisation from cloud → edge AI**

---

## 7. MQTT Backbone & System Integration

(Refer to Joanne’s diary for full details)

### Key Features
- MQTT-based communication between modules
- Standardised topics:
  - `user/id`
  - `scene/event`
  - `scene/summary`
  - `severity`

### Supporting Systems
- Live dashboard (WebSockets)
- Telegram alert service
- Cloud logging (Google Sheets)

### Key Achievements
- End-to-end pipeline tested:
  MQTT → Dashboard → Telegram → Cloud log

---

## 8. Optimisation & Edge Considerations

### 8.1 Computational Constraints
- Avoided heavy deep learning models where possible
- Selected lightweight models (LBPH, small VLM)

### 8.2 Latency Reduction
- Removed API calls (offline VLM)
- Local inference for faster response

### 8.3 Privacy
- No external image transmission
- All processing done locally

### 8.4 Modular Design
- Each module developed independently
- Allows flexible future integration

---

## 9. Testing Summary

### Successful Outcomes
- Face recognition works for trained users
- VLM provides scene understanding
- MQTT pipeline works end-to-end
- Alerts + dashboard + cloud logging functional

### Limitations
- Full system integration incomplete
- Performance overhead when running multiple modules
- VLM accuracy lower than cloud-based models

---

## 10. Key Learnings

Through this project, we learned:

- Edge systems require **trade-offs between accuracy and efficiency**
- Profiling and optimisation are essential, not optional
- Integration complexity is significantly higher than individual modules
- Cloud-based solutions are easier but not suitable for edge constraints

---

## 11. Future Improvements

- Improve full system integration across modules
- Optimise multi-module execution performance
- Improve VLM accuracy while maintaining efficiency
- Enhance robustness under real-world conditions

---

## 12. Conclusion

This project demonstrates the potential of a **context-aware edge AI system** that combines:
- identity (face recognition)
- context (VLM)

to enable more meaningful and personalised responses.

Although the system is still a prototype, it successfully shows:
→ how AI models can be adapted and optimised for **edge computing environments**

---

## 13. Repository Structure

```
face_recog/     → face recognition module
vlm/            → vision language model module
mqtt/           → communication + alerts
dashboard/      → web dashboard
```

---

## 14. Setup Instructions

Run:
```bash
bash setup.sh
```

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 15. Final Note

This repository serves as a **development diary**, documenting:
- what we built
- what we tested
- what issues we encountered
- how we optimised the system

This reflects our effort in designing a system that is:
→ **practical, efficient, and aligned with edge computing principles**
