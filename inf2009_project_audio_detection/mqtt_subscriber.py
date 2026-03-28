import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribe to all topics you're publishing
    client.subscribe("voice/#")

def on_message(client, userdata, msg):
    print(f"{msg.topic}: {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to the same broker (your Pi)
client.connect("192.168.137.44", 1883, 60)
client.loop_forever()