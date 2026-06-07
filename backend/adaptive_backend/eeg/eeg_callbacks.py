from __future__ import annotations

from typing import Any, Dict

from .resistance_analyzer import ResistanceQualityAnalyzer
from .runtime_metrics_store import RuntimeMetricsStore, runtime_metrics_store


class EEGCallbacks:
    def __init__(self, store: RuntimeMetricsStore = runtime_metrics_store) -> None:
        self.store = store
        self.analyzer = ResistanceQualityAnalyzer()

    def register(self, device: Any, productivity: Any, physiological_states: Any) -> None:
        device.set_on_connection_status_changed(self.on_connection_status)
        device.set_on_eeg(self.on_eeg)
        device.set_on_resistances(self.on_resistance)
        device.set_on_battery_charge_changed(self.on_battery)

        productivity.set_on_metrics_update(self.on_productivity)
        physiological_states.set_on_states(self.on_physiological)

    def on_connection_status(self, _device: Any, status: Any) -> None:
        connected = int(status) == 1
        print(f"[Capsule] connection status changed: {int(status)}")
        self.store.set_device_connected(connected)

    def on_eeg(self, _device: Any, eeg_data: Any) -> None:
        samples = eeg_data.get_samples_count()
        channels = eeg_data.get_channels_count()
        if samples <= 0 or channels <= 0:
            return

        last_sample_idx = samples - 1
        timestamp_milli = int(eeg_data.get_timestamp(last_sample_idx))

        processed = [float(eeg_data.get_processed_value(ch, last_sample_idx)) for ch in range(channels)]
        raw = [float(eeg_data.get_raw_value(ch, last_sample_idx)) for ch in range(channels)]

        packet = {
            "timestamp_milli": timestamp_milli,
            "samples_in_packet": samples,
            "channels": channels,
            "processed_last_sample": processed,
            "raw_last_sample": raw,
        }
        print(f"[Capsule] EEG packet ts={timestamp_milli} samples={samples} channels={channels}")
        self.store.update_eeg_packet(packet)

    def on_resistance(self, _device: Any, resistance_data: Any) -> None:
        values: Dict[str, float] = {}
        for idx in range(len(resistance_data)):
            values[resistance_data.get_channel_name(idx)] = float(resistance_data.get_value(idx))
        
        # Update raw resistance values
        self.store.update_resistance(values)
        
        # Analyze resistance quality
        channel_quality = self.analyzer.analyze_all(values)
        headset_ready = self.analyzer.is_headset_ready(channel_quality)
        
        # Update quality indicators
        self.store.update_channel_quality(channel_quality, headset_ready)
        
        # Print detailed resistance and quality info per-channel
        quality_stats = self.analyzer.get_quality_stats(channel_quality)
        print(f"[Capsule] resistance: {values}")
        # Per-channel verbose logging (Channel Name = Value Ω -> Quality)
        for ch, val in values.items():
            q = channel_quality.get(ch, "BAD")
            try:
                val_int = int(round(float(val)))
            except Exception:
                val_int = val
                print(f"[Capsule] {ch} = {val_int} Ω -> {q}")
        print(f"[Capsule] channel quality: {channel_quality}")
        print(f"[Capsule] quality summary: GOOD={quality_stats['GOOD']} WARNING={quality_stats['WARNING']} BAD={quality_stats['BAD']}")
        print(f"[Capsule] headset ready: {headset_ready}")

    def on_battery(self, _device: Any, charge: int) -> None:
        print(f"[Capsule] battery: {int(charge)}%")
        self.store.update_battery(int(charge))

    def on_productivity(self, _prod: Any, metrics: Any) -> None:
        data = {
            "timestamp_milli": int(metrics.timestampMilli),
            "focus": float(metrics.concentrationScore),
            "relaxation": float(metrics.relaxationScore),
            "fatigue": float(metrics.fatigueScore),
            "productivity": float(metrics.productivityScore),
            "current_value": float(metrics.currentValue),
            "alpha": float(metrics.alpha),
            "accumulated_fatigue": float(metrics.accumulatedFatigue),
        }
        print(
            "[Capsule] productivity "
            f"focus={data['focus']:.3f} relaxation={data['relaxation']:.3f} fatigue={data['fatigue']:.3f}"
        )
        self.store.update_productivity(data)

    def on_physiological(self, _phy: Any, states: Any) -> None:
        data = {
            "timestamp_milli": int(states.timestampMilli),
            "relaxation": float(states.relaxation),
            "fatigue": float(states.fatigue),
            "stress": float(states.stress),
            "concentration": float(states.concentration),
            "involvement": float(states.involvement),
            "none": float(states.none),
            "nfb_artifacts": bool(states.nfbArtifacts),
            "cardio_artifacts": bool(states.cardioArtifacts),
        }
        print(
            "[Capsule] physiological "
            f"relaxation={data['relaxation']:.3f} fatigue={data['fatigue']:.3f} stress={data['stress']:.3f}"
        )
        self.store.update_physiological(data)


callbacks = EEGCallbacks()
