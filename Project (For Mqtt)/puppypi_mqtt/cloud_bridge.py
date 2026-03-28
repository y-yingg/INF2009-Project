import json, requests
import paho.mqtt.client as mqtt
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
load_dotenv()

BROKER="localhost"
PORT=1883
DEVICE="pi5"

WEBAPP_URL = os.getenv("WEBAPP_URL")
if not WEBAPP_URL:
    raise RuntimeError("Missing WEBAPP_URL. Put it in .env")

TOPICS = [
  "user/id","scene/event","scene/summary","severity","scene/image_ref",
  "voice/intent","voice/speaker_id",
  "robot/task","robot/mode","nav/status","task/status","robot/target_locked",
  "emergency/refined_summary","emergency/recommendation"
]

state = {"user":None,"event":None,"summary":None,"severity":None,"image_ref":None}

def now():
    return datetime.now(timezone.utc).isoformat()

def parse_value(b):
    try:
        return json.loads(b.decode()).get("value")
    except:
        return b.decode()

def post_to_cloud(topic, value):
    payload = {
        "ts": now(),
        "topic": topic,
        "value": value,
        "device": DEVICE,
        "severity": state.get("severity"),
        "user": state.get("user"),
        "event": state.get("event"),
        "summary": state.get("summary"),
        "image_ref": state.get("image_ref"),
    }
    try:
        r = requests.post(WEBAPP_URL, json=payload, timeout=10)
        print("CLOUD:", r.status_code, topic)
    except Exception as e:
        print("CLOUD ERROR:", e)

def on_message(client, userdata, msg):
    v = parse_value(msg.payload)

    if msg.topic == "user/id": state["user"] = v
    elif msg.topic == "scene/event": state["event"] = v
    elif msg.topic == "scene/summary": state["summary"] = v
    elif msg.topic == "severity": state["severity"] = v
    elif msg.topic == "scene/image_ref": state["image_ref"] = v

    post_to_cloud(msg.topic, v)

client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, PORT, 60)
for t in TOPICS:
    client.subscribe(t)

print("Cloud Bridge running...")
client.loop_forever()
