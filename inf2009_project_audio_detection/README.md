# Audio Detection Module (Diary / Development Log)

## 1. Overview
This project implements a comprehensive audio detection system designed for the Hiwonder Puppypi (Raspberry Pi-based robot). 
It enables the robot to perceive its acoustic environment through three main capabilities:

1. Distance Estimation: Estimates the distance of the speaker based on audio volume (RMS).
2. Speaker Identification: Recognizes registered users via voice features.
3. Voice Command Detection: Detects wake words and specific control commands using offline speech recognition.

The system is modular, using MQTT for inter-process communication and logging, allowing for easy debugging and integration with other robot subsystems.

---
## 2. Implementation Details
**1. Distance Estimator `distance.py`**
- Algorithm: Calculates Root Mean Square (RMS) energy of audio chunks.
- Calibration: Uses a three-point calibration system (Close: 30cm, Medium: 1m, Far: 3m) to map RMS values to distance estimates.
- Output: Publishes distance (cm) and RMS values to the MQTT topic voice/distance.
- Hardware: Automatically selects USB audio input devices if available.

**2. Speaker Identification `speaker_id.py`**
- Feature Extraction: Uses MFCCs (via librosa) if available; falls back to FFT magnitude bins if librosa is missing.
- Matching: Compares extracted features against stored profiles (speaker_profiles.pkl) using cosine similarity.
- Registration: Includes a standalone script (register_speaker.py) to record and save user voice profiles.
- Output: Publishes identified speaker name to voice/speaker_id.

**3. Command Detector `commands.py`**
- Engine: Uses Vosk for offline speech-to-text.
- Logic:
  - Wake Words: Listens for "kitty", "dog", "puppy", etc.
  - Commands: Maps keywords to intents (e.g., "fetch", "clean_up", "come_here").
  - Emergency: Detects critical words like "help", "fire", "danger".
- Output: Publishes intent and transcribed text to voice/intent.

4. Communication (mqtt_subscriber.py & Modules)
- Broker: Connects to a local MQTT broker (default configured to 192.168.137.44).
- Topics:
  - voice/distance: Distance telemetry.
  - voice/speaker_id: Identification results.
  - voice/intent: Command intents.
  - voice/#: Wildcard subscription for debugging.
---
## 3. Integration Status
The system is designed to be orchestrated by a central `main.py`. The integration flow is as follows:
1. Audio Stream: `sounddevice` captures audio at 16kHz.
2. Chunk Processing: Each audio chunk is passed simultaneously to:
  - `DistanceEstimator.process_next()`
  - `SpeakerIdentifier.process_next()` (Buffers for utterance detection)
  - `CommandDetector.process_next()` (Vosk stream)
3. MQTT Loop: A background thread or non-blocking loop handles MQTT publishing/subscribing.
4. Status:
✅ Distance Estimation: Implemented & Calibratable.
✅ Speaker ID: Implemented & Persistent Storage.
✅ Command Detection: Implemented (Vosk dependent).
✅ MQTT Logging: Implemented.

