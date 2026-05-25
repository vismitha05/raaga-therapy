from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from adaptive_backend.db.base import Base


class EEGSession(Base):
    __tablename__ = "eeg_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    target_state: Mapped[str] = mapped_column(String(32), default="relaxed")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class BrainStateHistory(Base):
    __tablename__ = "brain_state_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("eeg_sessions.id"), index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    state: Mapped[str] = mapped_column(String(32), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    features: Mapped[dict] = mapped_column(JSON)


class RaagaMetadata(Base):
    __tablename__ = "raaga_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    state_category: Mapped[str] = mapped_column(String(32), index=True)
    day_part: Mapped[str] = mapped_column(String(32), index=True)
    tempo_category: Mapped[str] = mapped_column(String(32), index=True)
    intensity: Mapped[float] = mapped_column(Float)
    energy_level: Mapped[float] = mapped_column(Float)
    transition_tags: Mapped[dict] = mapped_column(JSON)


class TransitionHistory(Base):
    __tablename__ = "transition_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("eeg_sessions.id"), index=True)
    from_state: Mapped[str] = mapped_column(String(32))
    to_state: Mapped[str] = mapped_column(String(32))
    from_tempo: Mapped[str] = mapped_column(String(32))
    to_tempo: Mapped[str] = mapped_column(String(32))
    transition_stage: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), unique=True)
    preferred_target_state: Mapped[str] = mapped_column(String(32), default="relaxed")
    max_intensity: Mapped[float] = mapped_column(Float, default=0.8)
    transition_sensitivity: Mapped[float] = mapped_column(Float, default=0.5)


class PlaybackHistory(Base):
    __tablename__ = "playback_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("eeg_sessions.id"), index=True)
    raaga_name: Mapped[str] = mapped_column(String(128), index=True)
    tempo_level: Mapped[str] = mapped_column(String(32), index=True)
    intensity: Mapped[float] = mapped_column(Float)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EEGAnalytics(Base):
    __tablename__ = "eeg_analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("eeg_sessions.id"), index=True)
    metric_name: Mapped[str] = mapped_column(String(64), index=True)
    metric_value: Mapped[float] = mapped_column(Float)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
