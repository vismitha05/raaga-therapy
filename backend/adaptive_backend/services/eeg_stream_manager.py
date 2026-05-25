from collections import deque
from datetime import datetime


class EEGWindowBuffer:
    def __init__(self, window_seconds: int, sample_hz: int = 1):
        self.maxlen = window_seconds * sample_hz
        self.samples = deque(maxlen=self.maxlen)

    def append(self, sample: dict) -> None:
        sample = {**sample, "timestamp": datetime.utcnow()}
        self.samples.append(sample)

    def snapshot(self) -> list[dict]:
        return list(self.samples)

    def ready(self) -> bool:
        return len(self.samples) >= self.maxlen
