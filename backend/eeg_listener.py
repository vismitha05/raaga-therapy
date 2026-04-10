"""
eeg_listener.py
---------------
Connects to the Neiry EEG device via Lab Streaming Layer (LSL).
Continuously reads incoming EEG data (Alpha, Beta, Theta bands + brain state)
and exposes the latest sample through a thread-safe interface.

The Neiry device software streams pre-processed data; we simply consume it.
"""

import threading
import time
import math
import random
from typing import Optional

# Attempt to import pylsl; fall back to a simulator if not installed
try:
    from pylsl import StreamInlet, resolve_stream, StreamInfo
    LSL_AVAILABLE = True
except ImportError:
    LSL_AVAILABLE = False
    print("[EEGListener] pylsl not found — running in SIMULATION mode.")


# ─────────────────────────────────────────────
#  Data model
# ─────────────────────────────────────────────

class EEGSample:
    """Holds one snapshot of EEG frequency-band values and the detected state."""

    STATES = ["Focused", "Relaxed", "Fatigued"]

    def __init__(self, alpha: float, beta: float, theta: float, state: str):
        self.alpha = round(alpha, 4)
        self.beta = round(beta, 4)
        self.theta = round(theta, 4)
        self.state = state if state in self.STATES else "Relaxed"

    def to_dict(self) -> dict:
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "theta": self.theta,
            "state": self.state,
        }


# ─────────────────────────────────────────────
#  Simulator (used when no LSL stream is present)
# ─────────────────────────────────────────────

class EEGSimulator:
    """
    Generates realistic synthetic EEG data for development / demo purposes.
    Slowly drifts between brain states so the UI transitions are visible.
    """

    def __init__(self):
        self._t = 0.0          # internal time counter
        self._state_idx = 0    # index into STATES list
        self._state_timer = 0  # how long current state has been active

    def next_sample(self) -> EEGSample:
        self._t += 0.05
        self._state_timer += 1

        # Rotate state every ~8 seconds (160 ticks at 20 Hz)
        if self._state_timer > 160:
            self._state_idx = (self._state_idx + 1) % 3
            self._state_timer = 0

        state = EEGSample.STATES[self._state_idx]

        # Each state has characteristic band dominance
        if state == "Focused":
            alpha = 0.25 + 0.05 * math.sin(self._t * 1.3) + random.gauss(0, 0.01)
            beta  = 0.55 + 0.08 * math.sin(self._t * 2.1) + random.gauss(0, 0.02)
            theta = 0.20 + 0.04 * math.sin(self._t * 0.9) + random.gauss(0, 0.01)
        elif state == "Relaxed":
            alpha = 0.60 + 0.08 * math.sin(self._t * 0.7) + random.gauss(0, 0.02)
            beta  = 0.20 + 0.04 * math.sin(self._t * 1.5) + random.gauss(0, 0.01)
            theta = 0.30 + 0.05 * math.sin(self._t * 1.1) + random.gauss(0, 0.01)
        else:  # Fatigued
            alpha = 0.30 + 0.06 * math.sin(self._t * 0.5) + random.gauss(0, 0.01)
            beta  = 0.25 + 0.05 * math.sin(self._t * 0.8) + random.gauss(0, 0.01)
            theta = 0.65 + 0.09 * math.sin(self._t * 0.6) + random.gauss(0, 0.02)

        # Clamp to [0, 1]
        alpha = max(0.0, min(1.0, alpha))
        beta  = max(0.0, min(1.0, beta))
        theta = max(0.0, min(1.0, theta))

        return EEGSample(alpha, beta, theta, state)


# ─────────────────────────────────────────────
#  LSL Listener (real device)
# ─────────────────────────────────────────────

class LSLListener:
    """
    Resolves a running LSL stream (from Neiry software) and pulls samples.

    Expected stream format (configured in Neiry software):
      channel 0 → Alpha power
      channel 1 → Beta power
      channel 2 → Theta power
      channel 3 → State index (0=Focused, 1=Relaxed, 2=Fatigued)

    Adjust STATE_MAP and channel indices to match your Neiry export settings.
    """

    STATE_MAP = {0: "Focused", 1: "Relaxed", 2: "Fatigued"}

    def __init__(self, stream_type: str = "EEG", timeout: float = 5.0):
        print(f"[LSLListener] Searching for LSL stream of type '{stream_type}'...")
        streams = resolve_stream("type", stream_type, timeout=timeout)
        if not streams:
            raise RuntimeError(
                f"No LSL stream of type '{stream_type}' found. "
                "Ensure Neiry software is running and streaming."
            )
        self._inlet = StreamInlet(streams[0])
        info: StreamInfo = self._inlet.info()
        print(f"[LSLListener] Connected to '{info.name()}' @ {info.nominal_srate()} Hz")

    def next_sample(self) -> Optional[EEGSample]:
        sample, _ = self._inlet.pull_sample(timeout=0.0)  # non-blocking
        if sample is None:
            return None

        alpha = float(sample[0])
        beta  = float(sample[1])
        theta = float(sample[2])
        state_idx = int(round(sample[3]))
        state = self.STATE_MAP.get(state_idx, "Relaxed")

        return EEGSample(alpha, beta, theta, state)


# ─────────────────────────────────────────────
#  EEGListener — public interface
# ─────────────────────────────────────────────

class EEGListener:
    """
    Thread-safe wrapper that continuously reads from either the real LSL stream
    or the simulator, always keeping `latest` up to date.

    Usage:
        listener = EEGListener()
        listener.start()
        sample = listener.latest   # EEGSample or None
    """

    POLL_INTERVAL = 0.05   # seconds between polls (~20 Hz internal rate)

    def __init__(self):
        self.latest: Optional[EEGSample] = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        # Choose real LSL or simulator
        if LSL_AVAILABLE:
            try:
                self._source = LSLListener()
            except RuntimeError as exc:
                print(f"[EEGListener] LSL connection failed: {exc}")
                print("[EEGListener] Falling back to simulation mode.")
                self._source = EEGSimulator()
        else:
            self._source = EEGSimulator()

        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        """Begin background polling thread."""
        self._thread.start()
        print("[EEGListener] Background polling started.")

    def stop(self):
        """Signal the background thread to stop."""
        self._stop_event.set()

    def _run(self):
        """Inner loop: poll source, update self.latest."""
        while not self._stop_event.is_set():
            try:
                sample = self._source.next_sample()
                if sample is not None:
                    with self._lock:
                        self.latest = sample
            except Exception as exc:
                print(f"[EEGListener] Error reading sample: {exc}")
            time.sleep(self.POLL_INTERVAL)