"""
eeg_listener.py  —  Neiry Capsule EEG stream receiver
=======================================================

ARCHITECTURE
------------
Python is the TCP **server** on 127.0.0.1:5001.
The C++ bridge (CapsuleFilteredSignalExample.exe) is the **client**.

Wire format (C++ side):
  sprintf(buf, "%f,%f,...,%f\\n", ch0, ch1, ..., chN)
  → comma-separated floats, newline-terminated per sample batch

ROOT CAUSES FIXED IN THIS VERSION
----------------------------------
  RC-1  recv buffer was 1024 bytes — too small for multi-channel bursts.
        Fixed: 65536-byte recv buffer.

  RC-2  Connection socket had a recv timeout that fired between C++ bursts,
        causing Python to close the socket mid-session. C++'s next send
        hit a closed pipe → WinError 10054 on Windows.
        Fixed: NO recv timeout on the live connection socket.
        Instead a dedicated health-monitor thread watches last_data_time
        and only declares stale after STALE_DATA_TIMEOUT seconds of
        complete silence (not between bursts).

  RC-3  Server socket was closed/re-bound during reconnect attempts.
        C++ retried immediately and got "connection refused".
        Fixed: server socket stays open and listening the entire lifetime
        of the process. Only the per-connection socket is closed on error.

  RC-4  After disconnect Python slept before re-accepting, dropping C++
        reconnect attempts that arrived during the sleep.
        Fixed: accept() loop is non-blocking with a short poll; the server
        socket always has a queued backlog of 5.

  RC-5  No TCP_NODELAY — small packets were coalesced by Nagle's algorithm,
        adding latency and making partial-line parsing unreliable.
        Fixed: TCP_NODELAY set on both server and accepted socket.

  RC-6  EEG state detection used raw value comparison, broken across users.
        Fixed: uses classifier.classify_raw() (ratio-based).
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


# ── Configuration ─────────────────────────────────────────────────────────────

HOST             = "127.0.0.1"
PORT             = 5001
SAMPLE_RATE      = 256          # Hz – Neiry Capsule native sample rate
WINDOW_SIZE      = 256          # samples needed before each PSD computation
RECV_BUFSIZE     = 65536        # bytes per recv() call – large enough for bursts

# After this many seconds with zero new data on an established connection,
# declare it stale and drop it so C++ can reconnect cleanly.
# Set high (30 s) so normal inter-burst gaps don't trigger a false disconnect.
STALE_DATA_TIMEOUT = 30.0

# How long to wait for C++ to connect before switching to simulation.
CONNECT_TIMEOUT_S = 10.0

# Force simulation even when hardware is present.
FORCE_SIMULATE   = os.getenv("EEG_SIMULATE", "0") == "1"


# ── Data container ────────────────────────────────────────────────────────────

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


# ── Main listener ─────────────────────────────────────────────────────────────

class EEGListener:
    """
    Thread-safe EEG data source.

    Lifecycle
    ---------
    1. start() → spawns _accept_loop() daemon thread
    2. _accept_loop() keeps the server socket alive forever and accepts
       one connection at a time.
    3. Each accepted connection is handled by _handle_connection() in its
       own thread so the accept loop is never blocked.
    4. A health-monitor thread watches self._last_data_time and forcibly
       closes stale connections without touching the server socket.
    5. If no C++ connection arrives within CONNECT_TIMEOUT_S seconds,
       the simulator is started; it feeds the same _ingest() pipeline.
    """

    def __init__(self):
        self.latest: EEGSample | None = None
        self.simulating: bool = False

        self._buffer: list[float] = []
        self._lock = threading.Lock()

        # Shared across threads — when was data last received on active conn
        self._last_data_time: float = 0.0
        self._active_conn: socket.socket | None = None
        self._conn_lock = threading.Lock()

        # Server socket — created once, lives forever
        self._server: socket.socket | None = None
        self._got_first_connection = threading.Event()

    # ── Public API ─────────────────────────────────────────────────────────────

    def start(self):
        if FORCE_SIMULATE:
            print("[EEG] EEG_SIMULATE=1 → starting simulator directly.")
            self._start_simulator()
            return

        try:
            self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Disable Nagle: send small packets immediately
            self._server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self._server.bind((HOST, PORT))
            self._server.listen(5)          # backlog=5 so C++ reconnects queue up
            self._server.settimeout(1.0)    # non-blocking accept poll
            print(f"[EEG] Server listening on {HOST}:{PORT}")
        except OSError as e:
            print(f"[EEG] Cannot bind {HOST}:{PORT}: {e}. Starting simulator.")
            self._start_simulator()
            return

        threading.Thread(target=self._accept_loop,    daemon=True, name="eeg-accept").start()
        threading.Thread(target=self._health_monitor, daemon=True, name="eeg-health").start()

        # Give C++ CONNECT_TIMEOUT_S seconds to connect before falling back
        threading.Thread(target=self._fallback_timer, daemon=True, name="eeg-fallback").start()

    # ── Internal: connection lifecycle ─────────────────────────────────────────

    def _accept_loop(self):
        """Runs forever. Accepts one connection at a time."""
        while True:
            try:
                conn, addr = self._server.accept()
            except socket.timeout:
                continue        # poll again — keeps loop alive without blocking
            except OSError:
                break           # server socket closed (shouldn't happen)

            # Disable Nagle on the client socket too
            try:
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except OSError:
                pass

            print(f"[EEG] C++ bridge connected from {addr}")
            self._got_first_connection.set()

            # Close any existing stale connection cleanly
            with self._conn_lock:
                if self._active_conn:
                    try:
                        self._active_conn.close()
                    except OSError:
                        pass
                self._active_conn = conn
                self._last_data_time = time.time()

            # Handle the connection in a worker thread
            threading.Thread(
                target=self._handle_connection,
                args=(conn,),
                daemon=True,
                name="eeg-recv",
            ).start()

    def _handle_connection(self, conn: socket.socket):
        """
        Receives raw EEG lines from C++ until the connection is closed or
        goes stale. Does NOT set any timeout on recv() — the health monitor
        handles stale detection so we never interrupt a valid inter-burst gap.
        """
        pending = ""
        try:
            while True:
                # Check if this conn is still the active one
                with self._conn_lock:
                    if self._active_conn is not conn:
                        break   # superseded by a newer connection

                chunk = conn.recv(RECV_BUFSIZE)
                if not chunk:
                    # Graceful close from C++ side
                    print("[EEG] C++ closed the connection gracefully.")
                    break

                # Update liveness timestamp
                with self._conn_lock:
                    self._last_data_time = time.time()

                pending += chunk.decode(errors="ignore")
                lines = pending.split("\n")
                pending = lines.pop()   # keep incomplete trailing line

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        vals = [float(x) for x in line.split(",") if x.strip()]
                    except ValueError:
                        continue
                    if vals:
                        self._ingest(vals)

        except (ConnectionResetError, OSError) as e:
            print(f"[EEG] Connection error: {e}")
        finally:
            try:
                conn.close()
            except OSError:
                pass
            with self._conn_lock:
                if self._active_conn is conn:
                    self._active_conn = None
                    print("[EEG] Connection closed. Waiting for C++ to reconnect…")

    def _health_monitor(self):
        """
        Watches the active connection. If no data arrives for STALE_DATA_TIMEOUT
        seconds on an established connection, forcibly closes it so C++ can
        reconnect cleanly. Does NOT affect the server socket.
        """
        while True:
            time.sleep(5.0)
            with self._conn_lock:
                if self._active_conn is None:
                    continue
                idle = time.time() - self._last_data_time
                if idle > STALE_DATA_TIMEOUT:
                    print(f"[EEG Health] No data for {idle:.1f}s — closing stale connection.")
                    try:
                        self._active_conn.close()
                    except OSError:
                        pass
                    self._active_conn = None

    def _fallback_timer(self):
        """Start simulator if C++ never connects within CONNECT_TIMEOUT_S."""
        connected = self._got_first_connection.wait(timeout=CONNECT_TIMEOUT_S)
        if not connected:
            print(f"[EEG] No C++ connection after {CONNECT_TIMEOUT_S}s — starting simulator.")
            self._start_simulator()

    # ── Signal processing ──────────────────────────────────────────────────────

    def _ingest(self, values: list[float]):
        """Accumulate samples, compute Welch PSD, classify state."""
        with self._lock:
            self._buffer.extend(values)
            # Cap buffer to avoid unbounded growth
            if len(self._buffer) > WINDOW_SIZE * 8:
                self._buffer = self._buffer[-WINDOW_SIZE * 2:]

            if len(self._buffer) >= WINDOW_SIZE:
                signal = np.array(self._buffer[-WINDOW_SIZE:])
                freqs, psd = welch(signal, fs=SAMPLE_RATE,
                                   nperseg=min(WINDOW_SIZE, 128))
                alpha = _band_power(freqs, psd, 8,  12)
                beta  = _band_power(freqs, psd, 12, 30)
                theta = _band_power(freqs, psd, 4,   8)
                state = classify_raw(alpha, beta, theta)
                self.latest = EEGSample(alpha, beta, theta, state)

    # ── Simulator ─────────────────────────────────────────────────────────────

    def _start_simulator(self):
        self.simulating = True
        threading.Thread(target=self._simulate_loop, daemon=True, name="eeg-sim").start()

    def _simulate_loop(self):
        """
        Generates realistic synthetic EEG by summing sine waves at each band's
        centre frequency + Gaussian noise. Cycles Focused→Relaxed→Fatigued
        every 20 seconds, using the same _ingest() pipeline as real hardware.
        """
        print("[EEG Simulator] Running — Focused → Relaxed → Fatigued (20 s each)")
        t = 0.0
        dt = 1.0 / SAMPLE_RATE
        state_cycle = ["Focused", "Relaxed", "Fatigued"]
        state_idx = 0
        state_elapsed = 0.0
        state_duration = 20.0

        while True:
            target = state_cycle[state_idx % 3]
            if target == "Focused":
                amp = {"alpha": 0.4, "beta": 1.2, "theta": 0.3}
            elif target == "Relaxed":
                amp = {"alpha": 1.2, "beta": 0.4, "theta": 0.3}
            else:
                amp = {"alpha": 0.5, "beta": 0.3, "theta": 1.2}

            samples = []
            for _ in range(WINDOW_SIZE):
                s = (amp["alpha"] * math.sin(2 * math.pi * 10 * t)
                   + amp["beta"]  * math.sin(2 * math.pi * 20 * t)
                   + amp["theta"] * math.sin(2 * math.pi *  6 * t)
                   + random.gauss(0, 0.15))
                samples.append(s)
                t += dt

            self._ingest(samples)
            state_elapsed += WINDOW_SIZE * dt
            if state_elapsed >= state_duration:
                state_idx += 1
                state_elapsed = 0.0
                print(f"[EEG Simulator] → {state_cycle[state_idx % 3]}")

            time.sleep(WINDOW_SIZE * dt)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _band_power(freqs, psd, lo: float, hi: float) -> float:
    """
    Mean PSD in [lo, hi] Hz. Using the mean (not the sum) avoids classifying
    everyone as Focused — the beta band (12–30 Hz) is much wider than alpha/theta.
    """
    idx = np.logical_and(freqs >= lo, freqs <= hi)
    if not np.any(idx):
        return 0.0
    return float(np.mean(psd[idx]))