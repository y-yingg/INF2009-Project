import json
import time
import numpy as np
from vosk import Model, KaldiRecognizer

class CommandDetector:
    def __init__(self, mqtt_client):
        self.mqtt = mqtt_client
        self.rate = 16000
        self.model = Model("model")
        self.rec = KaldiRecognizer(self.model, self.rate)
        self.listening_for_command = False

        self.wake_words = ["kitty", "cat", "kitten", "puppy", "dog", "doggy"]
        self.commands = {
            "fetch": ["fetch", "get", "bring", "grab"],
            "clean_up": ["clean", "sweep", "vacuum", "tidy"],
            "come_here": ["come", "here", "approach", "arrive"],
            "search": ["search", "find", "locate", "where"]
        }
        self.emergency_words = ["help", "emergency", "scream", "fire", "stop", "danger"]

    def process_next(self, chunk):
        chunk_int16 = (chunk * 32768).astype(np.int16).tobytes()
        if self.rec.AcceptWaveform(chunk_int16):
            result = json.loads(self.rec.Result())
            text = result.get('text', '').lower()
            if text:
                # Print final transcription (clean)
                print(f"\n[Voice] {text}")

                # 1. Wake word
                if any(w in text for w in self.wake_words):
                    print("[Wake] Activated")
                    self.listening_for_command = True
                    # Check if command in same sentence
                    for cmd, keywords in self.commands.items():
                        if any(kw in text for kw in keywords):
                            print(f"[Command] {cmd}")
                            self._publish_intent(cmd, text)
                            self.listening_for_command = False
                    return

                # 2. Not activated but command spoken
                if not self.listening_for_command:
                    for cmd, keywords in self.commands.items():
                        if any(kw in text for kw in keywords):
                            print("[Wake] Please say wake word first")
                            break
                    return

                # 3. Activated: check emergency and commands
                if any(ew in text for ew in self.emergency_words):
                    print("[Emergency] !!!")
                    self._publish_intent("emergency", text)

                for cmd, keywords in self.commands.items():
                    if any(kw in text for kw in keywords):
                        print(f"[Command] {cmd}")
                        self._publish_intent(cmd, text)

        else:
            # Optional: print partial results for debugging
            partial = json.loads(self.rec.PartialResult())
            if partial.get('partial'):
                # Print partial on same line with carriage return (clean)
                print(f"\r[Partial] {partial['partial']:30}", end='')

    def _publish_intent(self, intent, text):
        msg = {"intent": intent, "text": text, "timestamp": time.time()}
        self.mqtt.publish("voice/intent", json.dumps(msg))
