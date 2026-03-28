let client = null;

const TOPIC_MAP = {
  "severity": "severity",
  "user/id": "user_id",
  "scene/event": "scene_event",
  "scene/summary": "scene_summary",
  "voice/intent": "voice_intent",
  "voice/speaker_id": "voice_speaker_id",
  "robot/task": "robot_task",
  "robot/mode": "robot_mode",
  "nav/status": "nav_status",
  "task/status": "task_status",
  "robot/target_locked": "target_locked",
  "scene/image_ref": "image_ref",
  "emergency/refined_summary": "em_refined",
  "emergency/recommendation": "em_reco",
};

function setValue(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value ?? "-";
  const ts = document.getElementById(id + "_ts");
  if (ts) ts.textContent = "Last update: " + new Date().toLocaleString();

  if (id === "severity") {
    const card = document.getElementById("sevCard");
    card.classList.remove("sev-normal", "sev-warning", "sev-urgent");
    const v = String(value || "").toUpperCase();
    if (v === "URGENT") card.classList.add("sev-urgent");
    else if (v === "WARNING") card.classList.add("sev-warning");
    else if (v) card.classList.add("sev-normal");
  }
}

function parsePayload(payload) {
  // expects {"value": "..."} but also handles plain text
  try {
    const obj = JSON.parse(payload);
    if (obj && typeof obj === "object" && "value" in obj) return obj.value;
    return obj;
  } catch {
    return payload;
  }
}

function connect() {
  const wsUrl = document.getElementById("wsUrl").value.trim();
  document.getElementById("status").textContent = "Connecting...";

  client = mqtt.connect(wsUrl);

  client.on("connect", () => {
    document.getElementById("status").textContent = "Connected";
    Object.keys(TOPIC_MAP).forEach(t => client.subscribe(t));
  });

  client.on("message", (topic, msg) => {
    const id = TOPIC_MAP[topic];
    if (!id) return;
    const value = parsePayload(msg.toString());
    setValue(id, value);
  });

  client.on("error", (err) => {
    document.getElementById("status").textContent = "Error: " + err.message;
  });

  client.on("close", () => {
    document.getElementById("status").textContent = "Disconnected";
  });
}

document.getElementById("btnConnect").addEventListener("click", connect);
