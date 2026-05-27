import asyncio
from datetime import datetime

from eeg_bridge import get_eeg_listener

from adaptive_backend.core.config import settings
from adaptive_backend.db.session import AsyncSessionLocal
from adaptive_backend.domain.enums import BrainState
from adaptive_backend.repositories.session_repository import SessionRepository
from adaptive_backend.services.brain_state_analyzer import detect_state, ui_state_label
from adaptive_backend.services.eeg_stream_manager import EEGWindowBuffer
from adaptive_backend.services.engines.playback_decision_engine import PlaybackDecisionEngine
from adaptive_backend.services.engines.state_transition_engine import StateTransitionEngine
from adaptive_backend.services.feature_extraction import extract_features
from adaptive_backend.services.realtime.websocket_manager import ConnectionManager
from adaptive_backend.services.session_manager import runtime_store


def _confidence_from_sample(alpha: float, beta: float, theta: float) -> float:
    total = alpha + beta + theta + 1e-9
    peak = max(alpha, beta, theta) / total
    return round(min(0.98, max(0.45, 0.45 + peak * 0.5)), 3)


class RealTimeMonitoringService:
    def __init__(self, ws_manager: ConnectionManager):
        self.ws_manager = ws_manager
        self.eeg_listener = get_eeg_listener()
        self.buffer = EEGWindowBuffer(window_seconds=settings.eeg_window_seconds)
        self.transition_engine = StateTransitionEngine()
        self.playback_engine = PlaybackDecisionEngine()
        self.running = False

    async def start(self):
        self.running = True
        while self.running:
            await self.tick()
            await asyncio.sleep(settings.eeg_poll_interval_seconds)

    async def tick(self):
        sample = self.eeg_listener.latest
        if sample is None:
            await self.ws_manager.broadcast(
                {
                    "eeg_status": "waiting",
                    "detected_state": "Connecting",
                    "confidence": 0,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            return

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

        if runtime_store.state.session_id is None:
            await self.ws_manager.broadcast(payload)
            return

        if not self.buffer.ready():
            await self.ws_manager.broadcast(payload)
            return

        window = self.buffer.snapshot()
        features = extract_features(window)
        detected_state, confidence = detect_state(features)
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
        await self.ws_manager.broadcast(payload)

        async with AsyncSessionLocal() as db:
            repo = SessionRepository(db)
            sid = runtime_store.state.session_id
            await repo.add_state_history(sid, detected_state.value, confidence, features)
            await repo.add_playback(sid, raaga["name"], next_tempo.value, float(raaga.get("intensity", 0.5)))

    def stop(self):
        self.running = False

    def latest_sample_dict(self) -> dict | None:
        sample = self.eeg_listener.latest
        if sample is None:
            return None
        return {
            **sample.to_dict(),
            "detected_state": ui_state_label(sample.state),
            "classifier_state": sample.state,
            "confidence": _confidence_from_sample(sample.alpha, sample.beta, sample.theta),
            "simulating": self.eeg_listener.simulating,
            "eeg_status": "live",
        }
