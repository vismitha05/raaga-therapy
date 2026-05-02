import socket
import threading
import numpy as np
from scipy.signal import welch


class EEGSample:
    def __init__(self, alpha, beta, theta, state):
        self.alpha = alpha
        self.beta = beta
        self.theta = theta
        self.state = state

    def to_dict(self):
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "theta": self.theta,
            "state": self.state
        }


class EEGListener:
    def __init__(self):
        self.latest = None
        self.buffer = []

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        HOST = '127.0.0.1'
        PORT = 5000

        s = socket.socket()
        s.bind((HOST, PORT))
        s.listen(1)

        print("[EEG] Waiting for C++ stream...")
        conn, _ = s.accept()
        print("[EEG] Connected to C++")

        while True:
            data = conn.recv(1024).decode()

            if not data:
                continue

            try:
                values = [float(x) for x in data.strip().split(",") if x]
                self.buffer.extend(values)

                if len(self.buffer) >= 256:
                    signal = np.array(self.buffer[-256:])

                    freqs, psd = welch(signal, fs=256)

                    alpha = self._band_power(freqs, psd, 8, 12)
                    beta  = self._band_power(freqs, psd, 12, 30)
                    theta = self._band_power(freqs, psd, 4, 8)

                    state = self._detect_state(alpha, beta, theta)

                    self.latest = EEGSample(alpha, beta, theta, state)

            except:
                continue

    def _band_power(self, freqs, psd, low, high):
        idx = np.logical_and(freqs >= low, freqs <= high)
        return np.sum(psd[idx])

    def _detect_state(self, alpha, beta, theta):
        if beta > alpha:
            return "Focused"
        elif alpha > beta:
            return "Relaxed"
        elif theta > alpha:
            return "Fatigued"
        return "Relaxed"