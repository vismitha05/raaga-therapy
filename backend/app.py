"""
app.py
------
Flask backend for the real-time Neiry neurofeedback system.

Endpoints:
  GET  /data          -> latest EEG sample + audio status + sim flag
  GET  /history       -> last 120 samples (for trend graphs)
  POST /mode          -> switch Study / Relax mode
  POST /volume        -> adjust audio volume
  GET  /health        -> liveness check + connection status

CORS is enabled so the React dev-server (port 3000) can reach this API.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
import collections

from eeg_listener import EEGListener
from audio_engine import AudioEngine

# ─── App setup ────────────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app)

# ─── Global singletons ────────────────────────────────────────────────────────

eeg   = EEGListener()
audio = AudioEngine(mode="Study")

HISTORY_MAXLEN = 120
history: collections.deque = collections.deque(maxlen=HISTORY_MAXLEN)
history_lock = threading.Lock()

# ─── Integration loop ────────────────────────────────────────────────────────

def _integration_loop():
    """5 Hz loop: EEG sample -> audio engine -> history buffer."""
    while True:
        sample = eeg.latest
        if sample is not None:
            audio.update(sample.state)
            entry = sample.to_dict()
            entry["timestamp"] = time.time()
            with history_lock:
                history.append(entry)
        time.sleep(0.2)

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    """Liveness + connection status."""
    return jsonify({
        "ok":        True,
        "simulating": eeg.simulating,
        "has_data":  eeg.latest is not None,
    })


@app.route("/data")
def get_data():
    """
    Latest EEG values + brain state + audio status.
    Response: { alpha, beta, theta, state, audio, simulating }
    """
    sample = eeg.latest
    if sample is None:
        # Return a pending status instead of a hard 503 so frontend can show
        # a "connecting…" spinner rather than a crash.
        return jsonify({
            "error":      "Waiting for EEG data…",
            "simulating": eeg.simulating,
        }), 503

    payload = sample.to_dict()
    payload["audio"]      = audio.status
    payload["simulating"] = eeg.simulating
    return jsonify(payload)


@app.route("/history")
def get_history():
    """Last 120 EEG snapshots for the trend graph."""
    with history_lock:
        data = list(history)
    return jsonify(data)


@app.route("/mode", methods=["POST"])
def set_mode():
    """Body: { "mode": "Study" | "Relax" }"""
    body = request.get_json(force=True, silent=True) or {}
    mode = body.get("mode", "Study")
    if mode not in ("Study", "Relax"):
        return jsonify({"error": "mode must be 'Study' or 'Relax'"}), 400
    audio.set_mode(mode)
    return jsonify({"mode": mode, "ok": True})


@app.route("/volume", methods=["POST"])
def set_volume():
    """Body: { "volume": 0.0–1.0 }"""
    body = request.get_json(force=True, silent=True) or {}
    try:
        vol = float(body.get("volume", 0.75))
    except (TypeError, ValueError):
        return jsonify({"error": "volume must be a float in [0, 1]"}), 400
    audio.set_volume(vol)
    return jsonify({"volume": vol, "ok": True})


# ─── Startup ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    eeg.start()

    t = threading.Thread(target=_integration_loop, daemon=True)
    t.start()

    print("[app] Neurofeedback backend → http://localhost:5000")
    print("[app] GET /health to check connection status.")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)