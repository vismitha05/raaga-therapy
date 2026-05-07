"""
eeg_listener.py
---------------
Listens on TCP 127.0.0.1:5001 for raw EEG samples streamed by the
Neiry Capsule C++ bridge (CapsuleFilteredSignalExample.exe).

The C++ side CONNECTS to us; we are the server.

Wire format (sent by C++ EXE):
  One or more comma-separated float values per line, terminated by \n
  e.g.  "-0.0012,0.0034,-0.0001,0.0056\n"

Processing:
  - Values are accumulated into a ring buffer (256 samples)
  - Once 256 samples exist, Welch PSD is computed (fs=256 Hz)
  - Alpha / Beta / Theta band powers are extracted
  - classifier.classify_raw() maps powers -> brain state

Fallback / simulation:
  When NO C++ connection is present, the listener runs a realistic
  EEG simulator so the rest of the pipeline (Flask API, audio engine,
  frontend) can be developed and tested without hardware.
  Set EEG_SIMULATE=1 in environment to force simulation even when the
  C++ bridge is reachable.
"""

import os
import socket
import threading
import time
import math
import random
import numpy as np
from scipy.signal import welch

from classifier import classify_raw


# ─── Config ──────────────────────────────────────────────────────────────────

HOST = "127.0.0.1"
PORT = 5001
SAMPLE_RATE = 256          # Hz – must match C++ EXE
WINDOW_SIZE = 256          # samples per PSD window
FORCE_SIMULATE = os.getenv("EEG_SIMULATE", "0") == "1"

# Accept timeout: if C++ doesn't connect within this many seconds,
# switch to simulation mode automatically.
CONNECT_TIMEOUT_S = 8


# ─── Data container ──────────────────────────────────────────────────────────

class EEGSample:
    def __init__(self, alpha: float, beta: float, theta: float, state: str):
        self.alpha = round(float(alpha), 6)
        self.beta  = round(float(beta),  6)
        self.theta = round(float(theta), 6)
        self.state = state

    def to_dict(self) -> dict:
        return {
            "alpha": self.alpha,
            "beta":  self.beta,
            "theta": self.theta,
            "state": self.state,
        }


# ─── EEG Listener ────────────────────────────────────────────────────────────

class EEGListener:
    """
    Thread-safe EEG data source.
    Automatically falls back to simulation if the C++ bridge does not connect.
    """

    def __init__(self):
        self.latest: EEGSample | None = None
        self._buffer: list[float] = []
        self._lock = threading.Lock()
        self._simulating = False

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self):
        """Launch background thread; returns immediately."""
        if FORCE_SIMULATE:
            print("[EEG] EEG_SIMULATE=1 → starting simulator directly.")
            self._start_simulator()
        else:
            t = threading.Thread(target=self._run_with_fallback, daemon=True)
            t.start()

    @property
    def simulating(self) -> bool:
        return self._simulating

    # ── Internal: real hardware path ─────────────────────────────────────────

    def _run_with_fallback(self):
        """
        Try to accept a C++ connection within CONNECT_TIMEOUT_S seconds.
        If none arrives, switch to simulation.
        """
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.settimeout(CONNECT_TIMEOUT_S)

        try:
            srv.bind((HOST, PORT))
            srv.listen(1)
            print(f"[EEG] Waiting for C++ bridge on {HOST}:{PORT} "
                  f"(timeout {CONNECT_TIMEOUT_S}s) …")
            try:
                conn, addr = srv.accept()
                srv.settimeout(None)
                print(f"[EEG] C++ bridge connected from {addr}")
                self._run_real(srv, conn)
            except socket.timeout:
                print("[EEG] No C++ connection – switching to EEG simulator.")
                srv.close()
                self._start_simulator()
        except OSError as e:
            print(f"[EEG] Could not bind {HOST}:{PORT} ({e}). Starting simulator.")
            self._start_simulator()

    def _run_real(self, srv_socket: socket.socket, conn: socket.socket):
        """
        Reads newline-delimited comma-separated float lines from the C++ bridge.
        On disconnect, waits for reconnect; falls back to simulator after 3 misses.
        """
        misses = 0
        while True:
            pending = ""
            try:
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        raise ConnectionResetError("empty recv")
                    pending += chunk.decode(errors="ignore")
                    lines = pending.split("\n")
                    pending = lines.pop()          # keep incomplete line

                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            vals = [float(x) for x in line.split(",") if x.strip()]
                        except ValueError:
                            continue
                        self._ingest(vals)

            except (ConnectionResetError, OSError) as e:
                misses += 1
                print(f"[EEG] C++ disconnected ({e}). Waiting to reconnect… "
                      f"(miss {misses}/3)")
                conn.close()
                if misses >= 3:
                    print("[EEG] 3 consecutive disconnects – switching to simulator.")
                    srv_socket.close()
                    self._start_simulator()
                    return
                # Wait for next connection
                try:
                    srv_socket.settimeout(CONNECT_TIMEOUT_S)
                    conn, addr = srv_socket.accept()
                    srv_socket.settimeout(None)
                    print(f"[EEG] Reconnected from {addr}")
                    misses = 0
                except socket.timeout:
                    print("[EEG] Reconnect timed out – switching to simulator.")
                    srv_socket.close()
                    self._start_simulator()
                    return

    def _ingest(self, values: list[float]):
        """Add raw voltage samples to the rolling buffer and recompute PSD."""
        with self._lock:
            self._buffer.extend(values)
            # Keep buffer from growing unboundedly
            if len(self._buffer) > WINDOW_SIZE * 4:
                self._buffer = self._buffer[-WINDOW_SIZE * 2:]

            if len(self._buffer) >= WINDOW_SIZE:
                signal = np.array(self._buffer[-WINDOW_SIZE:])
                freqs, psd = welch(signal, fs=SAMPLE_RATE,
                                   nperseg=min(WINDOW_SIZE, 128))
                alpha = self._band_power(freqs, psd, 8,  12)
                beta  = self._band_power(freqs, psd, 12, 30)
                theta = self._band_power(freqs, psd, 4,   8)
                state = classify_raw(alpha, beta, theta)
                self.latest = EEGSample(alpha, beta, theta, state)

    @staticmethod
    def _band_power(freqs, psd, lo: float, hi: float) -> float:
        idx = np.logical_and(freqs >= lo, freqs <= hi)
        return float(np.sum(psd[idx]))

    # ── Internal: simulator path ──────────────────────────────────────────────

    def _start_simulator(self):
        self._simulating = True
        t = threading.Thread(target=self._simulate_loop, daemon=True)
        t.start()

    def _simulate_loop(self):
        """
        Generate realistic synthetic EEG that cycles through states every ~20 s.
        Uses sine waves at band centre frequencies + pink noise.
        """
        print("[EEG] Simulator running – states cycle: Focused → Relaxed → Fatigued")
        t = 0.0
        dt = 1 / SAMPLE_RATE
        phase = 0.0
        state_cycle = ["Focused", "Relaxed", "Fatigued"]
        state_idx = 0
        state_duration = 20.0   # seconds per synthetic state
        state_elapsed = 0.0

        while True:
            current_target = state_cycle[state_idx % len(state_cycle)]

            # Amplitudes that produce the desired dominant band
            if current_target == "Focused":
                amp = {"alpha": 0.4, "beta": 1.2, "theta": 0.3}
            elif current_target == "Relaxed":
                amp = {"alpha": 1.2, "beta": 0.4, "theta": 0.3}
            else:  # Fatigued
                amp = {"alpha": 0.5, "beta": 0.3, "theta": 1.2}

            # Synthesize 256 samples
            samples = []
            for _ in range(WINDOW_SIZE):
                s = (amp["alpha"] * math.sin(2 * math.pi * 10  * t + phase)
                   + amp["beta"]  * math.sin(2 * math.pi * 20  * t + phase)
                   + amp["theta"] * math.sin(2 * math.pi * 6   * t + phase)
                   + random.gauss(0, 0.15))   # noise
                samples.append(s)
                t += dt

            self._ingest(samples)

            state_elapsed += WINDOW_SIZE * dt
            if state_elapsed >= state_duration:
                state_idx += 1
                state_elapsed = 0.0
                next_state = state_cycle[state_idx % len(state_cycle)]
                print(f"[EEG Simulator] → transitioning to: {next_state}")

            time.sleep(WINDOW_SIZE * dt)  # real-time pacing