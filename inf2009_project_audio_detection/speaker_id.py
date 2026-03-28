import numpy as np
import pickle
import os
import time
import json
import warnings
warnings.filterwarnings("ignore")

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False
    print("Librosa not found; using simple spectral features (less accurate).")

class SpeakerIdentifier:
    def __init__(self, mqtt_client, event_callback=None):
        self.mqtt = mqtt_client
        self.event_callback = event_callback  # optional function to call for events

        self.rate = 16000
        self.chunk_size = 1024

        self.profiles_file = "speaker_profiles.pkl"
        self.speaker_profiles = self.load_profiles()

        self.audio_buffer = []
        self.is_speaking = False
        self.silence_counter = 0
        self.silence_limit = int(0.5 * self.rate / self.chunk_size)

        self.identified = False
        self.current_speaker = None

    def load_profiles(self):
        if os.path.exists(self.profiles_file):
            with open(self.profiles_file, 'rb') as f:
                profiles = pickle.load(f)
                for name, samples in profiles.items():
                    for i in range(len(samples)):
                        feat = samples[i].astype(np.float64)
                        norm = np.linalg.norm(feat)
                        if norm > 1e-6:
                            samples[i] = feat / norm
                return profiles
        return {}

    def save_profiles(self):
        with open(self.profiles_file, 'wb') as f:
            pickle.dump(self.speaker_profiles, f)

    def extract_features(self, audio):
        if HAS_LIBROSA:
            mfccs = librosa.feature.mfcc(y=audio.astype(float), sr=self.rate, n_mfcc=13)
            mean = np.mean(mfccs, axis=1)
            std = np.std(mfccs, axis=1)
            feat = np.concatenate([mean, std])
        else:
            fft = np.fft.rfft(audio)
            magnitude = np.abs(fft)
            bins = 20
            feat = np.array([np.mean(magnitude[i::bins]) for i in range(bins)])
        feat = feat.astype(np.float64)
        norm = np.linalg.norm(feat)
        if norm > 1e-6:
            feat = feat / norm
        return feat.flatten()

    def identify_speaker(self, audio):
        if not self.speaker_profiles:
            return "unknown"
        chunk_size = int(3 * self.rate)
        chunks = np.array_split(audio, max(1, len(audio)//chunk_size))
        features_list = [self.extract_features(chunk) for chunk in chunks]
        features = np.mean(features_list, axis=0)

        THRESHOLD = 0.5
        best_name = "unknown"
        best_dist = float('inf')
        for name, samples in self.speaker_profiles.items():
            dists = []
            for sample in samples:
                sim = np.dot(features, sample)
                dists.append(1 - sim)
            avg_dist = np.mean(dists)
            if avg_dist < best_dist:
                best_dist = avg_dist
                best_name = name
        if best_dist > THRESHOLD:
            return "unknown"
        return best_name

    def process_utterance(self):
        if len(self.audio_buffer) == 0:
            return
        audio = np.concatenate([chunk.flatten() for chunk in self.audio_buffer])
        if len(audio) < int(1.5 * self.rate):
            return

        speaker = self.identify_speaker(audio)
        if speaker != "unknown":
            # Print a clean identification line (will appear above distance line)
            print(f"\n[Speaker] Identified: {speaker}")
            if self.event_callback:
                self.event_callback(f"Speaker identified: {speaker}")
            msg = {"speaker": speaker, "timestamp": time.time()}
            self.mqtt.publish("voice/speaker_id", json.dumps(msg))
            self.identified = True
            self.current_speaker = speaker
        else:
            print(f"\n[Speaker] Unknown")
            if self.event_callback:
                self.event_callback("Speaker unknown")
        self.audio_buffer = []

    def process_next(self, chunk):
        volume = np.sqrt(np.mean(chunk**2))
        if volume > 0.02:
            if not self.is_speaking:
                # Optionally print speech start (can be hidden)
                # print("\n[Speech] start")
                self.is_speaking = True
            self.audio_buffer.append(chunk)
            self.silence_counter = 0
        else:
            if self.is_speaking:
                self.silence_counter += 1
                if self.silence_counter > self.silence_limit:
                    # print("\n[Speech] end")
                    self.process_utterance()
                    self.is_speaking = False

    def register_speaker(self, name):
        import sounddevice as sd
        print(f"Recording sample for {name}...")
        devices = sd.query_devices()
        input_device = None
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0 and 'USB' in dev['name']:
                input_device = i
                break
        if input_device is None:
            input_device = sd.default.device[0]
        recording = sd.rec(int(3 * self.rate), samplerate=self.rate,
                           channels=1, dtype='float32', device=input_device)
        sd.wait()
        audio = recording.flatten()
        features = self.extract_features(audio)
        if name not in self.speaker_profiles:
            self.speaker_profiles[name] = []
        self.speaker_profiles[name].append(features)
        self.save_profiles()
        print(f"Speaker {name} now has {len(self.speaker_profiles[name])} samples.")
