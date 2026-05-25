from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from adaptive_backend.db.session import get_db_session
from adaptive_backend.repositories.session_repository import SessionRepository
from adaptive_backend.services.session_manager import runtime_store

router = APIRouter(prefix="/state", tags=["state"])


@router.get("/current")
async def get_current_state():
    s = runtime_store.state
    return {
        "timestamp": (s.last_update or datetime.utcnow()).isoformat(),
        "detected_state": s.detected_state.value,
        "target_state": s.target_state.value,
        "confidence": s.confidence,
    }


@router.get("/raaga")
async def get_current_raaga():
    s = runtime_store.state
    return {
        "raaga": s.active_raaga,
        "tempo": s.tempo_level.value,
        "transition_stage": s.transition_stage,
    }


@router.get("/tempo-progression")
async def get_tempo_progression():
    s = runtime_store.state
    return {
        "target_state": s.target_state.value,
        "detected_state": s.detected_state.value,
        "current_tempo": s.tempo_level.value,
        "transition_stage": s.transition_stage,
    }


@router.get("/analytics")
async def get_eeg_analytics():
    s = runtime_store.state
    return {
        "session_id": s.session_id,
        "confidence": s.confidence,
        "last_update": (s.last_update or datetime.utcnow()).isoformat(),
        "detected_state": s.detected_state.value,
        "target_state": s.target_state.value,
    }


@router.get("/transitions/{session_id}")
async def get_transition_history(session_id: int, db: AsyncSession = Depends(get_db_session)):
    repo = SessionRepository(db)
    rows = await repo.get_transitions(session_id)
    return [
        {
            "from_state": r.from_state,
            "to_state": r.to_state,
            "from_tempo": r.from_tempo,
            "to_tempo": r.to_tempo,
            "stage": r.transition_stage,
            "timestamp": r.created_at.isoformat(),
        }
        for r in rows
    ]
