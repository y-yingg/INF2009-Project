import sounddevice as sd
import queue
import time
import paho.mqtt.client as mqtt

from speaker_id import SpeakerIdentifier
from distance import DistanceEstimator
from commands import CommandDetector

# --- Shared audio queue ---
audio_queue = queue.Queue()

# --- MQTT client (use your Pi IP) ---
mqtt_client = mqtt.Client()
mqtt_client.connect("192.168.137.44", 1883, 60)
mqtt_client.loop_start()

# --- Initialize modules ---
speaker_id = SpeakerIdentifier(mqtt_client)  # event_callback optional
distance_estimator = DistanceEstimator(mqtt_client)
command_detector = CommandDetector(mqtt_client)

# --- Audio callback ---
def audio_callback(indata, frames, time_info, status):
    audio_queue.put(indata.copy())

# --- Auto-select USB microphone ---
devices = sd.query_devices()
input_device = None
for i, dev in enumerate(devices):
    if dev['max_input_channels'] > 0 and 'USB' in dev['name']:
        input_device = i
        break
if input_device is None:
    input_device = sd.default.device[0]
print(f"Using device {input_device}: {devices[input_device]['name']}")

# --- Calibrate distance (optional, you can comment out after first run) ---
distance_estimator.calibrate()

print("\n" + "="*50)
print("SYSTEM READY")
print("Speaker identification ? then command detection")
print("Say wake word: kitty, cat, puppy, dog, etc.")
print("="*50 + "\n")

# --- Main stream ---
with sd.InputStream(
    samplerate=16000,
    device=input_device,
    channels=1,
    dtype='float32',
    blocksize=1024,
    callback=audio_callback
):
    print("Listening...")
    try:
        while True:
            chunk = audio_queue.get()

            speaker_id.process_next(chunk)
            distance_estimator.process_next(chunk)

            if speaker_id.identified:
                command_detector.process_next(chunk)

            # Print status line (will be overwritten by distance line)
            if speaker_id.identified:
                status = f"Speaker: {speaker_id.current_speaker} | Mode: command"
            else:
                status = "Speaker: unknown | Mode: identification"
            # This will be updated by the distance line, so we can skip printing it.
            # Instead, we can print it once at the top and update only when changed.
            # For simplicity, we'll rely on the distance line and event prints.

            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\nStopping system...")
        mqtt_client.disconnect()
