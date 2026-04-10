"""
app.py
------
Flask backend for the real-time neurofeedback system.

Endpoints:
  GET  /data          → latest EEG sample + audio status
  GET  /history       → last N samples (for the history graph)
  POST /mode          → switch Study / Relax mode
  POST /volume        → adjust audio volume

CORS is enabled so the React dev-server (port 3000) can reach this API.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
import collections

from eeg_listener import EEGListener
from audio_engine import AudioEngine

# ─────────────────────────────────────────────
#  App setup
# ─────────────────────────────────────────────

app = Flask(__name__)
CORS(app)   # Allow cross-origin requests from React frontend

# ─────────────────────────────────────────────
#  Global singletons
# ─────────────────────────────────────────────

eeg = EEGListener()
audio = AudioEngine(mode="Study")

# Circular buffer: stores last 120 samples (~60 s at 2 Hz API polling)
HISTORY_MAXLEN = 120
history: collections.deque = collections.deque(maxlen=HISTORY_MAXLEN)
history_lock = threading.Lock()

# ─────────────────────────────────────────────
#  Background integration loop
# ─────────────────────────────────────────────

def _integration_loop():
    """
    Runs in a daemon thread.
    Every 200 ms: reads latest EEG sample → updates audio engine → appends to history.
    Decoupled from HTTP request cycle for consistent low-latency updates.
    """
    while True:
        sample = eeg.latest
        if sample is not None:
            # Feed state into audio engine (debounce logic lives inside AudioEngine)
            audio.update(sample.state)

            # Append timestamped snapshot to history buffer
            entry = sample.to_dict()
            entry["timestamp"] = time.time()
            with history_lock:
                history.append(entry)

        time.sleep(0.2)   # 5 Hz integration rate


# ─────────────────────────────────────────────
#  API Routes
# ─────────────────────────────────────────────

@app.route("/data")
def get_data():
    """
    Returns the latest EEG values, detected brain state, and audio status.
    Response schema:
      {
        alpha:   float,
        beta:    float,
        theta:   float,
        state:   str,         // "Focused" | "Relaxed" | "Fatigued"
        audio:   { track, state, mode, playing, volume }
      }
    """
    sample = eeg.latest
    if sample is None:
        return jsonify({"error": "No EEG data available yet."}), 503

    payload = sample.to_dict()
    payload["audio"] = audio.status
    return jsonify(payload)


@app.route("/history")
def get_history():
    """
    Returns up to the last 120 EEG snapshots for trend graphs.
    Each entry: { alpha, beta, theta, state, timestamp }
    """
    with history_lock:
        data = list(history)
    return jsonify(data)


@app.route("/mode", methods=["POST"])
def set_mode():
    """
    Body: { "mode": "Study" | "Relax" }
    Switches the adaptive audio mode.
    """
    body = request.get_json(force=True, silent=True) or {}
    mode = body.get("mode", "Study")
    if mode not in ("Study", "Relax"):
        return jsonify({"error": "mode must be 'Study' or 'Relax'"}), 400
    audio.set_mode(mode)
    return jsonify({"mode": mode, "ok": True})


@app.route("/volume", methods=["POST"])
def set_volume():
    """
    Body: { "volume": 0.0–1.0 }
    """
    body = request.get_json(force=True, silent=True) or {}
    try:
        vol = float(body.get("volume", 0.75))
    except (TypeError, ValueError):
        return jsonify({"error": "volume must be a float in [0, 1]"}), 400
    audio.set_volume(vol)
    return jsonify({"volume": vol, "ok": True})


# ─────────────────────────────────────────────
#  Startup
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # Start EEG listener thread
    eeg.start()

    # Start integration loop thread
    integration_thread = threading.Thread(target=_integration_loop, daemon=True)
    integration_thread.start()

    print("[app] Neurofeedback backend running on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)