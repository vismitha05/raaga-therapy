from datetime import datetime
from pydantic import BaseModel, Field

from adaptive_backend.domain.enums import BrainState, TempoLevel


class StartSessionRequest(BaseModel):
    user_id: str
    target_state: BrainState = BrainState.relaxed


class SessionResponse(BaseModel):
    session_id: int
    active: bool


class TargetStateRequest(BaseModel):
    target_state: BrainState


class BrainStateSnapshot(BaseModel):
    timestamp: datetime
    detected_state: BrainState
    confidence: float = Field(ge=0.0, le=1.0)
    target_state: BrainState


class PlaybackDecision(BaseModel):
    raaga_name: str
    tempo_level: TempoLevel
    intensity: float
    transition_stage: int


class LiveUpdate(BaseModel):
    eeg_status: str
    detected_state: BrainState
    target_state: BrainState
    active_raaga: str
    tempo_level: TempoLevel
    confidence: float
    transition_stage: int
    timestamp: datetime
