from speaker_id import SpeakerIdentifier
import sounddevice as sd

def main():
    # Create a dummy MQTT client (or pass None if not used)
    # We only need the registration method, so MQTT isn't essential here.
    import paho.mqtt.client as mqtt
    dummy_mqtt = mqtt.Client()
    # The SpeakerIdentifier expects a queue and mqtt client; we can pass a dummy queue.
    # We'll create a simple queue for compatibility, but it won't be used.
    import queue
    dummy_queue = queue.Queue()
    
    si = SpeakerIdentifier(dummy_queue, dummy_mqtt)
    
    while True:
        print("\n--- Speaker Registration ---")
        name = input("Enter speaker name (or 'quit' to exit): ").strip()
        if name.lower() == 'quit':
            break
        if name:
            si.register_speaker(name)
        else:
            print("Name cannot be empty.")

if __name__ == "__main__":
    main()