from __future__ import annotations

import time
from threading import Lock
from typing import Dict, Optional

from adaptive_backend.core.config import settings

from .capsule_adapter import CapsuleAdapter
from .runtime_metrics_store import runtime_metrics_store


class DeviceManager:
    def __init__(self, adapter: Optional[CapsuleAdapter] = None) -> None:
        self.adapter = adapter or CapsuleAdapter(
            scan_seconds=settings.capsule_scan_seconds,
            logs_dir=settings.capsule_logs_dir,
        )
        self._lock = Lock()
        self._state = "disconnected"
        self._last_error: Optional[str] = None

    def state(self) -> Dict[str, Optional[str]]:
        with self._lock:
            return {"state": self._state, "last_error": self._last_error}

    def start(self, preferred_serial: Optional[str] = None, bipolar_channels: bool = True) -> bool:
        with self._lock:
            self._state = "connecting"
            self._last_error = None

        serial = preferred_serial or settings.capsule_preferred_serial

        try:
            self.adapter.initialize_sdk()
            self.adapter.connect(
                serial=serial,
                bipolar_channels=bipolar_channels,
                discover_timeout_seconds=settings.capsule_discover_timeout_seconds,
                discover_retry_delay_seconds=settings.capsule_discover_retry_delay_seconds,
                discover_max_attempts=settings.capsule_discover_max_attempts,
            )
            self.adapter.start_stream()
        except Exception as exc:
            message = str(exc)
            runtime_metrics_store.set_error(message)
            with self._lock:
                self._state = "error"
                self._last_error = message
            print(f"[Capsule] start failed: {message}")
            return False

        with self._lock:
            self._state = "streaming"
        return True

    def stop(self) -> None:
        try:
            self.adapter.shutdown()
        except Exception as exc:
            runtime_metrics_store.set_error(str(exc))
            print(f"[Capsule] stop warning: {exc}")
        finally:
            with self._lock:
                self._state = "disconnected"

    def reconnect(self, retries: int = 3, delay_seconds: float = 2.0, preferred_serial: Optional[str] = None) -> bool:
        for attempt in range(1, retries + 1):
            print(f"[Capsule] reconnect attempt {attempt}/{retries}")
            self.stop()
            if self.start(preferred_serial=preferred_serial):
                return True
            time.sleep(delay_seconds)
        return False

    def is_streaming(self) -> bool:
        return self.state()["state"] == "streaming"


device_manager = DeviceManager()
