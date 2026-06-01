from dataclasses import dataclass
from datetime import datetime

from adaptive_backend.domain.enums import BrainState, TempoLevel


@dataclass
class RuntimeSessionState:
    session_id: int | None = None
    therapy_session_id: str | None = None
    user_id: str | None = None
    target_state: BrainState = BrainState.relaxed
    detected_state: BrainState = BrainState.relaxed
    confidence: float = 0.0
    active_raaga: str = ""
    tempo_level: TempoLevel = TempoLevel.low
    transition_stage: int = 0
    last_update: datetime | None = None
    therapy_active: bool = False
    current_cognitive_state: str = "A1"
    target_cognitive_state: str = "A1"
    session_duration_minutes: int = 0
    playlist_version: int = 0
    therapy_playlist: list | None = None


class SessionRuntimeStore:
    def __init__(self):
        self.state = RuntimeSessionState()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self.state, key, value)
        self.state.last_update = datetime.utcnow()


runtime_store = SessionRuntimeStore()
