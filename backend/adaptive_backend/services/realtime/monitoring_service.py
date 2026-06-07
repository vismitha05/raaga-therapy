import asyncio
from datetime import datetime
import json
import logging

from eeg_bridge import get_eeg_listener

from adaptive_backend.core.config import settings
from adaptive_backend.db.session import AsyncSessionLocal
from adaptive_backend.domain.enums import BrainState
from adaptive_backend.eeg.runtime_metrics_store import runtime_metrics_store
from adaptive_backend.repositories.session_repository import SessionRepository
from adaptive_backend.services.brain_state_analyzer import detect_state, ui_state_label
from adaptive_backend.services.eeg_stream_manager import EEGWindowBuffer
from adaptive_backend.services.engines.playback_decision_engine import PlaybackDecisionEngine
from adaptive_backend.services.engines.state_transition_engine import StateTransitionEngine
from adaptive_backend.services.feature_extraction import extract_features
from adaptive_backend.services.realtime.websocket_manager import ConnectionManager
from adaptive_backend.services.session_manager import runtime_store
from adaptive_backend.therapy.raaga_transition_engine import RaagaTransitionEngine, STATE_DESCRIPTIONS


def _confidence_from_sample(alpha: float, beta: float, theta: float) -> float:
    total = alpha + beta + theta + 1e-9
    peak = max(alpha, beta, theta) / total
    return round(min(0.98, max(0.45, 0.45 + peak * 0.5)), 3)


def _normalize_score(value) -> float:
    if value is None:
        return 0.0
    v = float(value)
    # Capsule metrics may come as 0..1 or 0..100 depending on source/calibration state.
    return max(0.0, min(1.0, v / 100.0 if v > 1.0 else v))


def _capsule_state_from_snapshot(snapshot: dict):
    focus = _normalize_score(snapshot.get("latest_focus"))
    relaxation = _normalize_score(snapshot.get("latest_relaxation"))
    fatigue = _normalize_score(snapshot.get("latest_fatigue"))
    stress = _normalize_score(snapshot.get("latest_stress"))

    has_metrics = any(v > 0 for v in (focus, relaxation, fatigue))
    if not has_metrics:
        return None

    mapped = {
        BrainState.focused: focus,
        BrainState.relaxed: relaxation,
        BrainState.sleepy: fatigue,
    }
    detected_state = max(mapped, key=mapped.get)

    base_confidence = max(mapped.values())
    # stress -> therapy adjustment: higher stress dampens confidence to slow tempo transitions.
    stress_factor = max(0.6, 1.0 - (0.4 * stress))
    adjusted_confidence = max(0.45, min(0.98, base_confidence * stress_factor + 0.35))

    return {
        "detected_state": detected_state,
        "confidence": round(adjusted_confidence, 3),
        "focus": focus,
        "relaxation": relaxation,
        "fatigue": fatigue,
        "stress": stress,
    }


def _capsule_ws_payload() -> dict:
    snapshot = runtime_metrics_store.snapshot()

    capsule_eeg_status = "waiting"
    if snapshot.get("device_connected") and snapshot.get("eeg_packets_received", 0) > 0:
        capsule_eeg_status = "live"

    return {
        "capsule_eeg_status": capsule_eeg_status,
        "battery": snapshot.get("battery_percent"),
        "resistance": snapshot.get("channel_resistance", {}),
        "channel_quality": snapshot.get("channel_quality", {}),
        "headset_ready": snapshot.get("headset_ready", False),
        "focus": snapshot.get("latest_focus"),
        "relaxation": snapshot.get("latest_relaxation"),
        "fatigue": snapshot.get("latest_fatigue"),
        "stress": snapshot.get("latest_stress"),
        "physiological_states": snapshot.get("physiological", {}),
    }


class RealTimeMonitoringService:
    def __init__(self, ws_manager: ConnectionManager, raaga_engine: RaagaTransitionEngine):
        self.ws_manager = ws_manager
        self.eeg_listener = get_eeg_listener()
        self.buffer = EEGWindowBuffer(window_seconds=settings.eeg_window_seconds)
        self.transition_engine = StateTransitionEngine()
        self.playback_engine = PlaybackDecisionEngine()
        self.raaga_engine = raaga_engine
        self.running = False

    async def start(self):
        self.running = True
        while self.running:
            await self.tick()
            await asyncio.sleep(settings.eeg_poll_interval_seconds)

    async def tick(self):
        # Temporary tracing logger for classification audit (remove after analysis)
        logger = logging.getLogger("classification_trace")
        if not logger.handlers:
            fh = logging.FileHandler("classification_trace.log")
            fh.setLevel(logging.INFO)
            fh.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(fh)
            logger.setLevel(logging.INFO)

        capsule_snapshot = runtime_metrics_store.snapshot()
        capsule_state = _capsule_state_from_snapshot(capsule_snapshot)
        headset_ready = capsule_snapshot.get("headset_ready", False)

        sample = self.eeg_listener.latest
        if capsule_state is None and sample is None:
            therapy_payload = self.raaga_engine.therapy_snapshot(headset_ready=headset_ready)
            runtime_metrics_store.update_therapy_status(therapy_payload)
            payload = {
                "eeg_status": "waiting",
                "detected_state": "Connecting",
                "confidence": 0,
                "timestamp": datetime.utcnow().isoformat(),
            }
            payload.update(_capsule_ws_payload())
            payload.update(therapy_payload)
            await self.ws_manager.broadcast(payload)
            return

        if capsule_state is not None:
            instant_state = capsule_state["detected_state"]
            instant_confidence = capsule_state["confidence"]
            ui_state = ui_state_label(instant_state.value)
            payload = {
                "eeg_status": "live",
                "detected_state": ui_state,
                "classifier_state": instant_state.value,
                "confidence": instant_confidence,
                "simulating": False,
                "timestamp": datetime.utcnow().isoformat(),
            }
            # Log that capsule metrics path was chosen for instant detection
            try:
                logger.info(json.dumps({
                    "ts": datetime.utcnow().isoformat(),
                    "event": "classification_instant",
                    "data_source": "CAPSULE_METRICS",
                    "focus": capsule_state.get("focus"),
                    "relaxation": capsule_state.get("relaxation"),
                    "fatigue": capsule_state.get("fatigue"),
                    "stress": capsule_state.get("stress"),
                    "classifier_state": instant_state.value,
                }))
            except Exception:
                pass
        else:
            self.buffer.append(sample.to_dict())
            instant_label = sample.state
            instant_confidence = _confidence_from_sample(sample.alpha, sample.beta, sample.theta)
            ui_state = ui_state_label(instant_label)
            payload = {
                "eeg_status": "live",
                "detected_state": ui_state,
                "classifier_state": instant_label,
                "alpha": sample.alpha,
                "beta": sample.beta,
                "theta": sample.theta,
                "confidence": instant_confidence,
                "simulating": self.eeg_listener.simulating,
                "timestamp": datetime.utcnow().isoformat(),
            }
            # Log that raw EEG path was chosen for instant detection
            try:
                logger.info(json.dumps({
                    "ts": datetime.utcnow().isoformat(),
                    "event": "classification_instant",
                    "data_source": "RAW_EEG",
                    "alpha": sample.alpha,
                    "beta": sample.beta,
                    "theta": sample.theta,
                    "classifier_state": instant_label,
                }))
            except Exception:
                pass

        payload.update(_capsule_ws_payload())

        if capsule_state is not None:
            cognitive_state = self.raaga_engine.derive_state(
                focus=capsule_state["focus"],
                relaxation=capsule_state["relaxation"],
                fatigue=capsule_state["fatigue"],
                stress=capsule_state["stress"],
                classifier_state=instant_state.value,
            )
        else:
            cognitive_state = self.raaga_engine.derive_state(
                alpha=sample.alpha,
                beta=sample.beta,
                theta=sample.theta,
                classifier_state=instant_label,
            )

        # Log the derived cognitive state and the inputs used
        try:
            if capsule_state is not None:
                logger.info(json.dumps({
                    "ts": datetime.utcnow().isoformat(),
                    "event": "derived_state",
                    "data_source": "CAPSULE_METRICS",
                    "focus": capsule_state.get("focus"),
                    "relaxation": capsule_state.get("relaxation"),
                    "fatigue": capsule_state.get("fatigue"),
                    "stress": capsule_state.get("stress"),
                    "classifier_state": instant_state.value,
                    "derived_state": cognitive_state,
                }))
            else:
                logger.info(json.dumps({
                    "ts": datetime.utcnow().isoformat(),
                    "event": "derived_state",
                    "data_source": "RAW_EEG",
                    "alpha": sample.alpha,
                    "beta": sample.beta,
                    "theta": sample.theta,
                    "classifier_state": instant_label,
                    "derived_state": cognitive_state,
                }))
        except Exception:
            pass

        stability_update = self.raaga_engine.update_stability(cognitive_state)
        payload.update(
            {
                "instant_cognitive_state": cognitive_state,
                "instant_cognitive_state_label": STATE_DESCRIPTIONS[cognitive_state],
                "state_stability": stability_update,
            }
        )

        if not runtime_store.state.therapy_active:
            therapy_payload = self.raaga_engine.therapy_snapshot(headset_ready=headset_ready)
            runtime_metrics_store.update_therapy_status(therapy_payload)
            payload.update(therapy_payload)
            await self.ws_manager.broadcast(payload)
            return

        if capsule_state is not None:
            detected_state = capsule_state["detected_state"]
            confidence = capsule_state["confidence"]
            features = {
                "focus": capsule_state["focus"],
                "relaxation": capsule_state["relaxation"],
                "fatigue": capsule_state["fatigue"],
                "stress": capsule_state["stress"],
                "source": "capsule_metrics",
            }
            # Log that runtime update will be driven by capsule metrics
            try:
                logger.info(json.dumps({
                    "ts": datetime.utcnow().isoformat(),
                    "event": "runtime_update",
                    "source": "CAPSULE_METRICS",
                    "detected_state": detected_state.value,
                    "confidence": confidence,
                }))
            except Exception:
                pass
        else:
            if not self.buffer.ready():
                therapy_payload = self.raaga_engine.therapy_snapshot(headset_ready=headset_ready)
                runtime_metrics_store.update_therapy_status(therapy_payload)
                payload.update(therapy_payload)
                await self.ws_manager.broadcast(payload)
                return
            window = self.buffer.snapshot()
            features = extract_features(window)
            detected_state, confidence = detect_state(features)
            # Log that runtime update will be driven by RAW_EEG (windowed features)
            try:
                logger.info(json.dumps({
                    "ts": datetime.utcnow().isoformat(),
                    "event": "runtime_update",
                    "source": "RAW_EEG_WINDOW",
                    "detected_state": detected_state.value,
                    "confidence": confidence,
                }))
            except Exception:
                pass

        ui_state = ui_state_label(detected_state.value)

        next_tempo = self.transition_engine.next_tempo(
            detected_state=detected_state,
            target_state=runtime_store.state.target_state,
            current_tempo=runtime_store.state.tempo_level,
            confidence=confidence,
        )
        raaga = self.playback_engine.decide(runtime_store.state.target_state, next_tempo)

        transition_stage = runtime_store.state.transition_stage
        if next_tempo != runtime_store.state.tempo_level:
            transition_stage += 1

        runtime_store.update(
            detected_state=detected_state,
            confidence=confidence,
            tempo_level=next_tempo,
            active_raaga=raaga["name"],
            transition_stage=transition_stage,
        )

        payload.update(
            {
                "detected_state": ui_state,
                "target_state": runtime_store.state.target_state.value,
                "active_raaga": raaga["name"],
                "tempo_level": next_tempo.value,
                "confidence": confidence,
                "transition_stage": transition_stage,
            }
        )

        if stability_update["state_changed"]:
            refreshed = self.raaga_engine.refresh_plan_for_new_state()
            if refreshed is not None:
                runtime_store.update(
                    current_cognitive_state=refreshed.source_state,
                    target_cognitive_state=refreshed.target_state,
                    playlist_version=refreshed.playlist_version,
                    therapy_playlist=[entry.to_dict() for entry in refreshed.playlist],
                )

        therapy_payload = self.raaga_engine.therapy_snapshot(headset_ready=headset_ready)
        runtime_metrics_store.update_therapy_status(therapy_payload)
        payload.update(therapy_payload)
        await self.ws_manager.broadcast(payload)

        if runtime_store.state.session_id is not None:
            async with AsyncSessionLocal() as db:
                repo = SessionRepository(db)
                sid = runtime_store.state.session_id
                await repo.add_state_history(sid, detected_state.value, confidence, features)
                await repo.add_playback(sid, raaga["name"], next_tempo.value, float(raaga.get("intensity", 0.5)))

    def stop(self):
        self.running = False

    def latest_sample_dict(self) -> dict | None:
        capsule_snapshot = runtime_metrics_store.snapshot()
        capsule_state = _capsule_state_from_snapshot(capsule_snapshot)

        if capsule_state is not None:
            payload = {
                "detected_state": ui_state_label(capsule_state["detected_state"].value),
                "classifier_state": capsule_state["detected_state"].value,
                "confidence": capsule_state["confidence"],
                "simulating": False,
                "eeg_status": "live",
            }
            payload.update(_capsule_ws_payload())
            payload.update(
                self.raaga_engine.therapy_snapshot(
                    headset_ready=capsule_snapshot.get("headset_ready", False)
                )
            )
            return payload

        sample = self.eeg_listener.latest
        if sample is None:
            return None
        payload = {
            **sample.to_dict(),
            "detected_state": ui_state_label(sample.state),
            "classifier_state": sample.state,
            "confidence": _confidence_from_sample(sample.alpha, sample.beta, sample.theta),
            "simulating": self.eeg_listener.simulating,
            "eeg_status": "live",
        }
        payload.update(_capsule_ws_payload())
        payload.update(
            self.raaga_engine.therapy_snapshot(
                headset_ready=capsule_snapshot.get("headset_ready", False)
            )
        )
        return payload
