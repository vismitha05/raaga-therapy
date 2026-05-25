from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from adaptive_backend.db.session import get_db_session
from adaptive_backend.domain.schemas.schemas import StartSessionRequest, SessionResponse, TargetStateRequest
from adaptive_backend.repositories.session_repository import SessionRepository
from adaptive_backend.services.session_manager import runtime_store

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/start", response_model=SessionResponse)
async def start_session(payload: StartSessionRequest, db: AsyncSession = Depends(get_db_session)):
    repo = SessionRepository(db)
    row = await repo.create_session(payload.user_id, payload.target_state.value)
    runtime_store.update(session_id=row.id, user_id=row.user_id, target_state=payload.target_state, transition_stage=0)
    return SessionResponse(session_id=row.id, active=row.active)


@router.post("/{session_id}/stop", response_model=SessionResponse)
async def stop_session(session_id: int, db: AsyncSession = Depends(get_db_session)):
    repo = SessionRepository(db)
    row = await repo.stop_session(session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    runtime_store.update(session_id=None)
    return SessionResponse(session_id=row.id, active=row.active)


@router.post("/{session_id}/target")
async def set_target_state(session_id: int, payload: TargetStateRequest, db: AsyncSession = Depends(get_db_session)):
    repo = SessionRepository(db)
    row = await repo.set_target_state(session_id, payload.target_state.value)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    runtime_store.update(target_state=payload.target_state)
    return {"ok": True, "target_state": payload.target_state.value}
