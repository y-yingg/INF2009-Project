import json
import requests
import paho.mqtt.client as mqtt
import time
import os
from dotenv import load_dotenv

load_dotenv()

last_alert_ts = 0
ALERT_COOLDOWN_SEC = 15

BROKER = "localhost"
PORT = 1883

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload, timeout=15)

def send_telegram_photo_file(bot_token: str, chat_id: str, caption: str, file_path: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    try:
        with open(file_path, "rb") as f:
            files = {"photo": ("image.jpg", f, "image/jpeg")}
            data = {"chat_id": chat_id, "caption": caption}
            resp = requests.post(url, data=data, files=files, timeout=30)
        return resp.status_code == 200
    except Exception as e:
        # send_telegram_message(bot_token, chat_id, caption + f"\n(Sorry, failed to send image: {e})")
        send_telegram_message(caption + f"\n(Sorry, failed to send image: {e})")
        return False

def parse_value(payload_bytes: bytes):
    try:
        return json.loads(payload_bytes.decode("utf-8")).get("value")
    except Exception:
        return payload_bytes.decode("utf-8")

state = {"user":None, "event":None, "summary":None, "severity":None, "image_ref":None, "voice_intent":None}

def build_msg():
    lines = ["?? PuppyPi Alert"]
    if state["user"]: lines.append(f"User: {state['user']}")
    if state["severity"]: lines.append(f"Severity: {state['severity']}")
    if state["event"]: lines.append(f"Scene event: {state['event']}")
    if state["summary"]: lines.append(f"Scene summary: {state['summary']}")
    if state["image_ref"]: lines.append(f"Image ref: {state['image_ref']}")
    if state.get("voice_intent"): lines.append(f"Voice intent: {state['voice_intent']}")
    return "\n".join(lines)

def image_ref_to_path(image_ref: str):
    if not image_ref:
        return None
    s = str(image_ref).strip()
    if s.startswith("local:"):
        return s.replace("local:", "", 1)
    if s.startswith("file://"):
        return s.replace("file://", "", 1)
    # if it's a plain absolute path like /home/jo/inf2009/capture.jpg
    if s.startswith("/"):
        return s
    return None

# Trigger conditions
def is_help_intent(v):
    if not v:
        return False
    s = str(v).strip().lower()
    return s in ["help", "help me", "emergency"] or "help" in s

def on_message(client, userdata, msg):
    global last_alert_ts  # <--- IMPORTANT

    v = parse_value(msg.payload)
    print("MQTT IN:", msg.topic, v)

    # Update state
    if msg.topic == "user/id": 
        state["user"] = v
    elif msg.topic == "scene/event": 
        state["event"] = v
    elif msg.topic == "scene/summary": 
        state["summary"] = v
    elif msg.topic == "severity": 
        state["severity"] = v
    elif msg.topic == "scene/image_ref": 
        state["image_ref"] = v
    elif msg.topic == "voice/intent":
        # optional: store it if you want it in the message
        state["voice_intent"] = v

    # Trigger alert on URGENT OR help intent
    should_alert = (msg.topic == "severity" and v == "URGENT") or \
                   (msg.topic == "voice/intent" and is_help_intent(v))

    if should_alert:
        now_ts = time.time()
        if now_ts - last_alert_ts < ALERT_COOLDOWN_SEC:
            print("Skip alert (cooldown)")
            return
        last_alert_ts = now_ts

        caption = build_msg()
        path = image_ref_to_path(state.get("image_ref"))

        if path:
            ok = send_telegram_photo_file(BOT_TOKEN, CHAT_ID, caption, path)
            if not ok:
                send_telegram_message(caption)
        else:
            send_telegram_message(caption)


client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, PORT, 60)

for t in ["user/id","scene/event","scene/summary","severity","scene/image_ref","voice/intent","voice/speaker_id"]:
    client.subscribe(t)

print("Telegram alert service running...")
client.loop_forever()
