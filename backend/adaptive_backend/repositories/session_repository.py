from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adaptive_backend.domain.models.models import EEGSession, BrainStateHistory, TransitionHistory, PlaybackHistory


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, user_id: str, target_state: str) -> EEGSession:
        row = EEGSession(user_id=user_id, target_state=target_state)
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def stop_session(self, session_id: int) -> EEGSession | None:
        row = await self.db.get(EEGSession, session_id)
        if not row:
            return None
        row.active = False
        row.ended_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def get_session(self, session_id: int) -> EEGSession | None:
        return await self.db.get(EEGSession, session_id)

    async def set_target_state(self, session_id: int, target_state: str) -> EEGSession | None:
        row = await self.db.get(EEGSession, session_id)
        if not row:
            return None
        row.target_state = target_state
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def add_state_history(self, session_id: int, state: str, confidence: float, features: dict) -> None:
        self.db.add(BrainStateHistory(session_id=session_id, state=state, confidence=confidence, features=features))
        await self.db.commit()

    async def add_transition(self, session_id: int, from_state: str, to_state: str, from_tempo: str, to_tempo: str, stage: int) -> None:
        self.db.add(TransitionHistory(session_id=session_id, from_state=from_state, to_state=to_state, from_tempo=from_tempo, to_tempo=to_tempo, transition_stage=stage))
        await self.db.commit()

    async def add_playback(self, session_id: int, raaga_name: str, tempo_level: str, intensity: float) -> None:
        self.db.add(PlaybackHistory(session_id=session_id, raaga_name=raaga_name, tempo_level=tempo_level, intensity=intensity))
        await self.db.commit()

    async def get_transitions(self, session_id: int) -> list[TransitionHistory]:
        result = await self.db.execute(select(TransitionHistory).where(TransitionHistory.session_id == session_id).order_by(TransitionHistory.created_at.desc()))
        return list(result.scalars().all())
