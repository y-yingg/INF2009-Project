import numpy as np
import time
import json

class DistanceEstimator:
    def __init__(self, mqtt_client):
        self.mqtt = mqtt_client
        self.rate = 16000
        self.chunk_size = 1024
        self.calibration = { #adjust the values later calibration for mic testing
            "close": 0.04,
            "medium": 0.0175,
            "far": 0.01
        }
        self.history = []

    def estimate_distance(self, rms):
        if rms > self.calibration["close"]:
            return 30
        elif rms > self.calibration["medium"]:
            ratio = (self.calibration["close"] - rms) / (self.calibration["close"] - self.calibration["medium"])
            return 30 + 70 * ratio
        elif rms > self.calibration["far"]:
            ratio = (self.calibration["medium"] - rms) / (self.calibration["medium"] - self.calibration["far"])
            return 100 + 200 * ratio
        else:
            return None

    def calibrate(self):
        print("\n=== Distance Calibration ===")
        input("Place mic 30 cm from speaker and press Enter (speak continuously)...")
        rms_close = self.record_rms()
        self.calibration["close"] = float(rms_close)
        print(f"RMS at 30 cm: {rms_close:.4f}")

        input("Place mic 1 m from speaker and press Enter...")
        rms_medium = self.record_rms()
        self.calibration["medium"] = float(rms_medium)
        print(f"RMS at 1 m: {rms_medium:.4f}")

        input("Place mic 3 m from speaker and press Enter...")
        rms_far = self.record_rms()
        self.calibration["far"] = float(rms_far)
        print(f"RMS at 3 m: {rms_far:.4f}")

        print("Calibration complete!")
        print(self.calibration)

    def record_rms(self, duration=3):
        import sounddevice as sd
        devices = sd.query_devices()
        input_device = None
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0 and 'USB' in dev['name']:
                input_device = i
                break
        if input_device is None:
            input_device = sd.default.device[0]
        recording = sd.rec(int(duration * self.rate), samplerate=self.rate,
                           channels=1, dtype='float32', device=input_device)
        sd.wait()
        return float(np.sqrt(np.mean(recording**2)))

    def process_next(self, chunk):
        rms = np.sqrt(np.mean(chunk**2))
        self.history.append(rms)
        if len(self.history) > 5:
            self.history.pop(0)
        avg_rms = np.mean(self.history)

        distance = self.estimate_distance(avg_rms)
        if distance is not None:
            # Update the same line with a carriage return
            print(f"\rDistance: {distance:3.0f} cm | RMS: {avg_rms:.4f}", end='')
            msg = {"distance_cm": float(distance), "rms": float(avg_rms), "timestamp": time.time()}
            self.mqtt.publish("voice/distance", json.dumps(msg))
        else:
            print(f"\rToo far/silent (RMS: {avg_rms:.4f})", end='')
