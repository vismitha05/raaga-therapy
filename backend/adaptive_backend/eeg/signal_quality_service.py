from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List

from .runtime_metrics_store import runtime_metrics_store


class ChannelQuality:
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


@dataclass(frozen=True)
class SignalQualityThresholds:
    # Lower resistance is better. Units follow SDK callback values.
    green_max: float = 10_000.0
    yellow_max: float = 30_000.0


class SignalQualityService:
    def __init__(self, thresholds: SignalQualityThresholds = SignalQualityThresholds()) -> None:
        self.thresholds = thresholds

    def classify_channel(self, resistance_value: float) -> str:
        if resistance_value <= self.thresholds.green_max:
            return ChannelQuality.GREEN
        if resistance_value <= self.thresholds.yellow_max:
            return ChannelQuality.YELLOW
        return ChannelQuality.RED

    def get_channel_status(self) -> Dict[str, Dict[str, float | str]]:
        snapshot = runtime_metrics_store.snapshot()
        resistances: Dict[str, float] = snapshot.get("channel_resistance", {}) or {}

        status: Dict[str, Dict[str, float | str]] = {}
        for channel, value in resistances.items():
            numeric_value = float(value)
            status[channel] = {
                "resistance": numeric_value,
                "quality": self.classify_channel(numeric_value),
            }
        return status

    def overall_headset_readiness(self) -> Dict[str, object]:
        channel_status = self.get_channel_status()
        if not channel_status:
            return {
                "ready": False,
                "reason": "no_resistance_data",
                "green": 0,
                "yellow": 0,
                "red": 0,
                "channels": 0,
            }

        qualities: List[str] = [item["quality"] for item in channel_status.values()]
        green = sum(1 for q in qualities if q == ChannelQuality.GREEN)
        yellow = sum(1 for q in qualities if q == ChannelQuality.YELLOW)
        red = sum(1 for q in qualities if q == ChannelQuality.RED)
        total = len(qualities)

        # Ready when no RED channels and majority GREEN.
        ready = red == 0 and green >= max(1, (total + 1) // 2)

        reason = "ok" if ready else "improve_contact"
        if red > 0:
            reason = "red_channels_present"

        return {
            "ready": ready,
            "reason": reason,
            "green": green,
            "yellow": yellow,
            "red": red,
            "channels": total,
        }

    def websocket_payload(self) -> Dict[str, object]:
        channel_status = self.get_channel_status()
        readiness = self.overall_headset_readiness()

        return {
            "type": "signal_quality",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signal_quality": {
                "channels": channel_status,
                "overall": readiness,
            },
        }


signal_quality_service = SignalQualityService()
