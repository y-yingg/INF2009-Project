# Joanne's Diary (MQTT Backbone + Cloud Connectivity + Telegram Alerts)
Author: Joanne Liao  

> This README is a detailed diary of what I implemented, tested, and debugged (communication backbone + external communication).  
> Focus: **coding / setup / testing** only.

---

## 1) What I was responsible for
- Set up the **MQTT communication backbone** (topic structure + publish/subscribe testing).
- Build a **coded MQTT dashboard website** (custom HTML/JS) to display live “PuppyPi stats”.
- Build **Telegram alert service** that subscribes to MQTT and sends alerts:
  - include detected user
  - include scene event + summary
  - include severity (URGENT)
  - include image (optional) via `scene/image_ref`
- Implement required **cloud logging/dashboards** using a free cloud approach:
  - Google Apps Script Web App endpoint
  - Google Sheet as cloud log database + dashboard

---

## 2) Hardware / environment used for development
I did not have the Hiwonder PuppyPi robot to test. I used:
- **Raspberry Pi 5** as the stand-in “on-robot” computer
- Laptop browser to open the dashboard website

This allowed me to validate the full pipeline:
**MQTT publish → dashboard update → Telegram alert (with image) → cloud log row in Google Sheet**.

---

## 3) MQTT Backbone: setup + verification

### 3.1 Installed Mosquitto and CLI tools
Installed:
- `mosquitto` (broker)
- `mosquitto_pub` / `mosquitto_sub` (CLI test tools)

### 3.2 Verified MQTT is working
Used 2 terminals:
- Terminal A: `mosquitto_sub -t test/topic`
- Terminal B: `mosquitto_pub -t test/topic -m hello`

This confirmed broker publish/subscribe works before writing Python code.

### 3.3 Topic structure used
Core topics used in my testing (aligned to architecture diagram + integration needs):
- `user/id`
- `scene/event`
- `scene/summary`
- `severity` (NORMAL / WARNING / URGENT)
- `scene/image_ref` (local file path or URL reference)
- `voice/intent`
- `voice/speaker_id`
- `robot/task`
- `robot/mode`

Status topics displayed in dashboard:
- `nav/status`
- `task/status`
- `robot/target_locked`

Emergency loop-back topics supported:
- `emergency/refined_summary`
- `emergency/recommendation`

Payload format standardized as JSON like:
```json
{"value": "..."}
```
so Python + dashboard parsing stays consistent.

---

## 4) Telegram Alert Service (MQTT → Telegram)

### 4.1 First run error: missing `paho-mqtt`
When I ran:
```bash
python3 telegram_alert_service.py
```
I got:
- `ModuleNotFoundError: No module named 'paho'`

### 4.2 Fix: create a Python virtual environment
I created and used a venv to avoid “installed into wrong python” issues:
```bash
cd ~/puppypi_mqtt
python3 -m venv .venv
source .venv/bin/activate
pip install paho-mqtt requests
```

### 4.3 Confirmed “listener behavior” is correct
After launching, the script prints “running” and then waits.  
This is expected because it only reacts when MQTT messages arrive.

### 4.4 Publisher bug discovered: only 1 topic appeared
When I tested publishing via `sim_publish.py`, only `user/id` appeared in:
```bash
mosquitto_sub -t "#" -v
```
even though my script published multiple topics.

**Cause:** `paho-mqtt` publishes asynchronously; the script disconnected too fast, so only the first message was flushed.

### 4.5 Fix: flush publish properly (reliable multi-topic publish)
I updated the simulator to:
- `client.loop_start()`
- `qos=1`
- `wait_for_publish()`
- small delay between publishes
- short sleep before disconnect

After this, all topics consistently appeared.

### 4.6 Telegram image not sending (initially)
Telegram was sending text alerts, but not the image.

**Cause:** `scene/image_ref` contained a local path like:
- `local:/tmp/fall.jpg` or `file:///...`
Telegram can’t fetch local filesystem paths from my Pi.

### 4.7 Fix: upload image bytes via `sendPhoto`
I implemented Telegram photo sending as a multipart upload:
- parse `scene/image_ref`
- if `local:` / `file://` / absolute path → open file and upload bytes
- else if `http/https` URL → can send as URL
- fallback to text only if upload fails

For testing, I used a real file path:
- `/home/jo/inf2009/capture.jpg`
and published:
- `scene/image_ref = local:/home/jo/inf2009/capture.jpg`

Telegram successfully sent **photo + caption**.

### 4.8 Trigger logic expanded: “help” intent + severity URGENT
Originally, trigger = `severity == URGENT`.  
I updated it so alerts trigger on:
- `severity == URGENT` **OR**
- `voice/intent` contains “help”

### 4.9 Duplicate alert issue (sent twice)
After adding both triggers, I received 2 alerts:
1) when `voice/intent=help`
2) when `severity=URGENT`

**Fix:** added a cooldown/de-dup mechanism:
- `last_alert_ts`
- `ALERT_COOLDOWN_SEC = 15`
If an alert was just sent, the next trigger within 15 seconds is ignored.

This stopped spam and kept the demo clean.

### 4.10 Documentation
After being done with the telegram alert setup, I setup a documentation on how I setup the bot to be able to receive alerts: https://docs.google.com/document/d/1VxpVLeNj_gL_3C0oUJzNiwwE6WHgert9GZ0Fyb34Ojo/edit?usp=sharing

---

## 5) Coded MQTT Dashboard Website (Custom HTML/JS)

### 5.1 Why custom HTML (vs Node-RED)
I chose custom HTML/JS because:
- easy to **zip and share**
- no “install Node-RED plugins + import flows” complexity
- meets “coded website” requirement clearly

### 5.2 Browser needs MQTT WebSockets
Browsers can’t connect to MQTT TCP 1883 directly, so I enabled WebSockets on Mosquitto at **port 9001**.

### 5.3 Mosquitto WebSockets config attempt + failure
My first WebSockets config caused:
- `mosquitto.service` failed to restart

From logs it was failing right after loading:
- `/etc/mosquitto/conf.d/websockets.conf`

This happened because I had prior lab edits to Mosquitto listener settings, and the new listener config conflicted.

### 5.4 Fix: corrected listener config and verified ports
After fixing the Mosquitto config, I verified:
```bash
sudo ss -ltnp | grep mosquitto
```
It showed both:
- `:1883` (mqtt)
- `:9001` (websockets)

### 5.5 Implemented dashboard files
Created folder `puppypi_dashboard/`:
- `index.html` (cards for each topic)
- `app.js` (mqtt.js subscribe logic, JSON parsing, severity highlighting)

Dashboard usage:
- open website: `http://<PI_IP>:8000`
- set broker: `ws://<PI_IP>:9001`
- click **Connect**
- publish topics and see live updates

### 5.6 Hosting website
Hosted using:
```bash
cd ~/puppypi_dashboard
python3 -m http.server 8000
```

Tested from laptop browser: page loads, connects, updates live.

---

## 6) Cloud logging / dashboards (Required)

### 6.1 Apps Script access issue (initial)
Initially I had trouble opening Apps Script with an Error 400 on the website, so I switched to a clearer flow:
- create Apps Script project properly and deploy web app endpoint

### 6.2 Chosen cloud approach (free)
Used **Google Apps Script Web App** + **Google Sheets**:
- free
- easy for teammates/prof to view logs
- Google Sheet acts as the “dashboard” (filters/charts)

### 6.3 Implemented Apps Script (Option B: standalone project)
Implemented:
- `doPost(e)` reads JSON and appends a row into a fixed sheet by `SpreadsheetApp.openById(SHEET_ID)`
- auto-creates `logs` tab if missing
- writes header row if empty
- `doGet(e)` returns a simple “OK” text for quick browser check

Deployment settings chosen for easy access:
- Execute as: **Me**
- Who has access: **Anyone**

### 6.4 Tested Apps Script endpoint
Tested by:
- opening the deployed URL in browser (doGet) to confirm it’s live
- sending a POST from Pi using `curl` to confirm `{"ok":true}`
- confirmed the Sheet tab `logs` received new rows

### 6.5 Implemented Cloud Bridge (MQTT → Apps Script Web App)
Wrote `cloud_bridge.py` that:
- subscribes to MQTT topics
- for each message, POSTs JSON to the Apps Script Web App URL
- includes useful context fields (device, user, severity, event, summary, image_ref)

Validated cloud logging end-to-end:
- publish MQTT messages
- see rows appended into Google Sheet

Link of Google Sheet: https://docs.google.com/spreadsheets/d/1QdU6wPMbbpqHYVisY1Y0S4c65k0XexS-UKLaG8Qn3gw/edit?usp=sharing

---

## 7) Packaging / handoff

### 7.1 Transferred project from Pi to laptop
After everything worked, I copied the project folders to my laptop for sharing.

### 7.2 Identified and fixed secret leakage
Originally, bot token + chat id were hardcoded.  
For safe sharing, I moved secrets into `.env`.

Files:
- `.env` (private; NOT shared)
- `.env.example` (safe to share)

### 7.3 Created requirements.txt
Created:
```txt
paho-mqtt
requests
python-dotenv
```

---

## 8) Final demo test run (recording checklist)
To show all systems working (dashboard + Telegram + cloud logs):

### Terminal A (Telegram service)
```bash
cd ~/puppypi_mqtt
source .venv/bin/activate
python telegram_alert_service.py
```

### Terminal B (Cloud bridge)
```bash
cd ~/puppypi_mqtt
source .venv/bin/activate
python cloud_bridge.py
```

### Terminal C (Dashboard server)
```bash
cd ~/puppypi_dashboard
python3 -m http.server 8000
```

### Browser
- Open: `http://<PI_IP>:8000`
- Connect WS: `ws://<PI_IP>:9001`

### Publish URGENT test event (Terminal D)
Test 1:
```bash
mosquitto_pub -t user/id -m '{"value":"grandma"}'
mosquitto_pub -t scene/event -m '{"value":"fall_detected"}'
mosquitto_pub -t scene/summary -m '{"value":"User fell near sofa"}'
mosquitto_pub -t scene/image_ref -m '{"value":"local:/home/jo/inf2009/fallinggrandma.jpg"}'
mosquitto_pub -t voice/intent -m '{"value":"help"}'
mosquitto_pub -t voice/speaker_id -m '{"value":"grandma"}'
mosquitto_pub -t severity -m '{"value":"URGENT"}'
```

Test 2:
```bash
mosquitto_pub -t user/id -m '{"value":"grandpa"}'
mosquitto_pub -t scene/event -m '{"value":"fall_detected"}'
mosquitto_pub -t scene/summary -m '{"value":"User fell near sofa"}'
mosquitto_pub -t scene/image_ref -m '{"value":"local:/home/jo/inf2009/capture.jpg"}'
mosquitto_pub -t voice/intent -m '{"value":"help"}'
mosquitto_pub -t voice/speaker_id -m '{"value":"grandma"}'
mosquitto_pub -t severity -m '{"value":"URGENT"}'
```

Expected results (what I verified):
- Dashboard updates with the latest values ✅
- Telegram sends alert (with image if file exists) ✅
- Google Sheet appends log rows ✅

---

## 9) Shutdown steps after testing
Stop Python scripts with `Ctrl+C`.

Stop Mosquitto:
```bash
sudo systemctl stop mosquitto
```
(Optional) prevent auto-start:
```bash
sudo systemctl disable mosquitto
```

---

## 10) Bugs encountered + fixes (summary)
- `ModuleNotFoundError: paho` → fixed with venv + `pip install paho-mqtt`
- Only 1 topic published by simulator → fixed with `loop_start`, `wait_for_publish`, QoS, sleeps
- Telegram image not sent (local path) → fixed by uploading file bytes via `sendPhoto`
- Duplicate alerts (help + urgent) → fixed with cooldown `ALERT_COOLDOWN_SEC`
- Mosquitto restart failure after websocket config → fixed listener config; verified `1883` + `9001`
- Cloud logging required → implemented Apps Script Web App + `cloud_bridge.py` logging to Google Sheet
- Secrets in code → moved to `.env` + `.env.example` for safe sharing
