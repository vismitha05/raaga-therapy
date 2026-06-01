from __future__ import annotations

import threading
import time
from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Literal, Optional


@dataclass
class RuntimeMetricsSnapshot:
    device_connected: bool = False
    device_info: Dict[str, Any] = field(default_factory=dict)
    last_error: Optional[str] = None

    battery_percent: Optional[int] = None
    channel_resistance: Dict[str, float] = field(default_factory=dict)
    channel_quality: Dict[str, Literal["GOOD", "WARNING", "BAD"]] = field(default_factory=dict)
    headset_ready: bool = False

    last_eeg_packet: Optional[Dict[str, Any]] = None
    eeg_packets_received: int = 0
    eeg_packet_timestamps: List[float] = field(default_factory=list)

    productivity: Dict[str, Any] = field(default_factory=dict)
    physiological: Dict[str, Any] = field(default_factory=dict)

    latest_focus: Optional[float] = None
    latest_relaxation: Optional[float] = None
    latest_fatigue: Optional[float] = None
    latest_stress: Optional[float] = None
    therapy_status: Dict[str, Any] = field(default_factory=dict)


class RuntimeMetricsStore:
    def __init__(self, max_eeg_timestamps: int = 5000) -> None:
        self._lock = threading.Lock()
        self._snapshot = RuntimeMetricsSnapshot()
        self._eeg_ts_ring: Deque[float] = deque(maxlen=max_eeg_timestamps)

    def set_device_connected(self, connected: bool, device_info: Optional[Dict[str, Any]] = None) -> None:
        with self._lock:
            self._snapshot.device_connected = connected
            if device_info:
                self._snapshot.device_info = dict(device_info)

    def set_error(self, error_message: str) -> None:
        with self._lock:
            self._snapshot.last_error = error_message

    def update_battery(self, battery_percent: int) -> None:
        with self._lock:
            self._snapshot.battery_percent = int(battery_percent)

    def update_resistance(self, values: Dict[str, float]) -> None:
        with self._lock:
            self._snapshot.channel_resistance = dict(values)

    def update_channel_quality(
        self, 
        channel_quality: Dict[str, Literal["GOOD", "WARNING", "BAD"]], 
        headset_ready: bool
    ) -> None:
        """Update channel quality indicators and headset ready state."""
        with self._lock:
            self._snapshot.channel_quality = dict(channel_quality)
            self._snapshot.headset_ready = headset_ready

    def update_eeg_packet(self, packet: Dict[str, Any]) -> None:
        now_ts = time.time()
        with self._lock:
            self._snapshot.last_eeg_packet = dict(packet)
            self._snapshot.eeg_packets_received += 1
            self._eeg_ts_ring.append(now_ts)
            self._snapshot.eeg_packet_timestamps = list(self._eeg_ts_ring)

    def update_productivity(self, metrics: Dict[str, Any]) -> None:
        with self._lock:
            self._snapshot.productivity = dict(metrics)
            self._snapshot.latest_focus = metrics.get("focus", self._snapshot.latest_focus)
            self._snapshot.latest_relaxation = metrics.get("relaxation", self._snapshot.latest_relaxation)
            self._snapshot.latest_fatigue = metrics.get("fatigue", self._snapshot.latest_fatigue)

    def update_physiological(self, metrics: Dict[str, Any]) -> None:
        with self._lock:
            self._snapshot.physiological = dict(metrics)
            self._snapshot.latest_relaxation = metrics.get("relaxation", self._snapshot.latest_relaxation)
            self._snapshot.latest_fatigue = metrics.get("fatigue", self._snapshot.latest_fatigue)
            self._snapshot.latest_stress = metrics.get("stress", self._snapshot.latest_stress)

    def update_therapy_status(self, therapy_status: Dict[str, Any]) -> None:
        with self._lock:
            self._snapshot.therapy_status = dict(therapy_status)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return deepcopy(self._snapshot.__dict__)


runtime_metrics_store = RuntimeMetricsStore()
