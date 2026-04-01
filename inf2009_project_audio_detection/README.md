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

**4. Communication `mqtt_subscriber.py` & Modules**
- Broker: Connects to a local MQTT broker (default configured to `192.168.137.44`).
- Topics:
  - `voice/distance`: Distance telemetry.
  - `voice/speaker_id`: Identification results.
  - `voice/intent`: Command intents.
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
---
## 4. Setup Instructions
**1. Install System Dependencies**
```bash
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-pip python3-venv libatlas-base3
```
**2. Create Virtual Environment**
```bash
python3 -m venv audio_env
source audio_env/bin/activate
```
**3. Install Python Packages**
```bash
pip install numpy sounddevice paho-mqtt
pip install librosa  # Optional but recommended for Speaker ID
pip install vosk     # Required for Command Detection

OR

pip install -r requirements.text
```
---
## 5. Optimization and Edge Considerations
**Optimization**
- Feature Normalization: Speaker features are L2-normalized to ensure cosine similarity works effectively regardless of volume.
- Buffering: Speaker ID buffers audio (~1.5s) before processing to ensure enough data for accurate identification.
- Fallback Mechanisms: Speaker ID gracefully degrades to FFT features if `librosa` is not installed, ensuring compatibility on resource-constrained devices.
**Edge Cases & Limitations**
- Noise Sensitivity: Distance estimation relies on RMS. Background noise may falsely indicate a closer distance. Mitigation: Noise gating implemented in Speaker ID (volume > 0.02).
- Wake Word False Positives: Simple string matching on transcribed text may trigger on similar-sounding words. Mitigation: Vosk confidence thresholds could be added.
- Latency: Vosk processing is computationally heavy. On older Pi models, there may be a delay between speech and intent recognition.
- Mic Selection: Code prioritizes USB mics. If using the Pi's GPIO header mic (I2S), the device selection logic in `distance.py` and `speaker_id.py` may need adjustment.
