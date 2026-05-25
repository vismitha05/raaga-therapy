import asyncio
from datetime import datetime

from eeg_listener import EEGListener

from adaptive_backend.core.config import settings
from adaptive_backend.db.session import AsyncSessionLocal
from adaptive_backend.domain.enums import BrainState
from adaptive_backend.repositories.session_repository import SessionRepository
from adaptive_backend.services.brain_state_analyzer import detect_state
from adaptive_backend.services.eeg_stream_manager import EEGWindowBuffer
from adaptive_backend.services.engines.playback_decision_engine import PlaybackDecisionEngine
from adaptive_backend.services.engines.state_transition_engine import StateTransitionEngine
from adaptive_backend.services.feature_extraction import extract_features
from adaptive_backend.services.realtime.websocket_manager import ConnectionManager
from adaptive_backend.services.session_manager import runtime_store


class RealTimeMonitoringService:
    def __init__(self, ws_manager: ConnectionManager):
        self.ws_manager = ws_manager
        self.eeg_listener = EEGListener()  # Existing bridge class: unchanged.
        self.buffer = EEGWindowBuffer(window_seconds=settings.eeg_window_seconds)
        self.transition_engine = StateTransitionEngine()
        self.playback_engine = PlaybackDecisionEngine()
        self.running = False

    async def start(self):
        self.eeg_listener.start()
        self.running = True
        while self.running:
            await self.tick()
            await asyncio.sleep(settings.eeg_poll_interval_seconds)

    async def tick(self):
        sample = self.eeg_listener.latest
        if sample is None:
            return

        self.buffer.append(sample.to_dict())
        if not self.buffer.ready() or runtime_store.state.session_id is None:
            return

        window = self.buffer.snapshot()
        features = extract_features(window)
        detected_state, confidence = detect_state(features)

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

        payload = {
            "eeg_status": "live",
            "detected_state": detected_state.value,
            "target_state": runtime_store.state.target_state.value,
            "active_raaga": raaga["name"],
            "tempo_level": next_tempo.value,
            "confidence": confidence,
            "transition_stage": transition_stage,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.ws_manager.broadcast(payload)

        async with AsyncSessionLocal() as db:
            repo = SessionRepository(db)
            sid = runtime_store.state.session_id
            await repo.add_state_history(sid, detected_state.value, confidence, features)
            await repo.add_playback(sid, raaga["name"], next_tempo.value, float(raaga.get("intensity", 0.5)))

    def stop(self):
        self.running = False
