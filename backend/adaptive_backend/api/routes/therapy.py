from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from adaptive_backend.api.dependencies import raaga_transition_engine, runtime_metrics_store
from adaptive_backend.services.session_manager import runtime_store
from adaptive_backend.therapy.raaga_transition_engine import (
    COGNITIVE_STATES,
    STATE_DESCRIPTIONS,
    STATE_ORDER,
)

router = APIRouter(prefix="/therapy", tags=["therapy"])

active_sessions: Dict[str, Dict[str, Any]] = {}


class TherapySessionStartRequest(BaseModel):
    target_state: str = Field(..., description="One of T1, T2, A1, A2, B1, B2")
    duration_minutes: int = Field(..., ge=1, le=180)


class TherapyPlaybackUpdate(BaseModel):
    session_id: str
    track_index: int
    elapsed_seconds: float
    is_playing: bool


def _current_or_default_state() -> str:
    state = raaga_transition_engine.stability.accepted_state
    return state if state in STATE_ORDER else "A1"


def _serialize_session(session_id: str, *, now: Optional[datetime] = None) -> Dict[str, Any]:
    session = active_sessions[session_id]
    therapy_snapshot = raaga_transition_engine.therapy_snapshot(
        headset_ready=runtime_metrics_store.snapshot().get("headset_ready", False),
        now=now,
    )
    return {
        "session_id": session_id,
        "created_at": session["created_at"].isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "source_state": session["source_state"],
        "source_state_label": STATE_DESCRIPTIONS[session["source_state"]],
        "target_state": session["target_state"],
        "target_state_label": STATE_DESCRIPTIONS[session["target_state"]],
        "duration_minutes": session["duration_minutes"],
        "playlist": therapy_snapshot.get("playlist", []),
        "playlist_version": therapy_snapshot.get("playlist_version", 0),
        "time_period": therapy_snapshot.get("time_period"),
        "current_track": therapy_snapshot.get("current_track"),
        "upcoming_track": therapy_snapshot.get("upcoming_track"),
        "current_raaga": therapy_snapshot.get("current_raaga"),
        "upcoming_raaga": therapy_snapshot.get("upcoming_raaga"),
        "session_progress_percent": therapy_snapshot.get("session_progress_percent", 0),
        "transition_path": therapy_snapshot.get("transition_path", []),
        "crossfade_seconds": therapy_snapshot.get("crossfade_seconds", 0),
        "headset_ready": therapy_snapshot.get("headset_ready", False),
        "headset_message": therapy_snapshot.get("headset_message", ""),
    }


@router.get("/states")
async def therapy_states() -> Dict[str, List[Dict[str, str]]]:
    return {"states": [COGNITIVE_STATES[code].to_dict() for code in STATE_ORDER]}


@router.post("/session/start")
async def start_therapy_session(request: TherapySessionStartRequest) -> Dict[str, Any]:
    target_state = request.target_state.upper()
    if target_state not in STATE_ORDER:
        raise HTTPException(status_code=400, detail=f"Invalid target state: {request.target_state}")

    metrics_snapshot = runtime_metrics_store.snapshot()
    headset_ready = metrics_snapshot.get("headset_ready", False)
    current_state = _current_or_default_state()
    session_id = str(uuid.uuid4())

    try:
        plan = raaga_transition_engine.start_session(
            current_state=current_state,
            target_state=target_state,
            duration_minutes=request.duration_minutes,
            headset_ready=headset_ready,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    active_sessions[session_id] = {
        "created_at": datetime.utcnow(),
        "source_state": current_state,
        "target_state": target_state,
        "duration_minutes": request.duration_minutes,
        "playback_updates": [],
    }

    runtime_store.update(
        therapy_session_id=session_id,
        therapy_active=True,
        current_cognitive_state=current_state,
        target_cognitive_state=target_state,
        session_duration_minutes=request.duration_minutes,
        playlist_version=plan.playlist_version,
        therapy_playlist=[entry.to_dict() for entry in plan.playlist],
        active_raaga=plan.playlist[0].raaga if plan.playlist else "",
    )
    therapy_status = raaga_transition_engine.therapy_snapshot(headset_ready=headset_ready)
    runtime_metrics_store.update_therapy_status(therapy_status)
    return _serialize_session(session_id)


@router.get("/session/{session_id}")
async def get_therapy_session(session_id: str) -> Dict[str, Any]:
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return _serialize_session(session_id)


@router.post("/playback/update")
async def update_playback_progress(update: TherapyPlaybackUpdate) -> Dict[str, Any]:
    if update.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    active_sessions[update.session_id]["playback_updates"].append(
        {
            "track_index": update.track_index,
            "elapsed_seconds": update.elapsed_seconds,
            "is_playing": update.is_playing,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    return {"status": "ok"}


@router.post("/session/stop/{session_id}")
async def stop_therapy_session(session_id: str) -> Dict[str, Any]:
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    active_sessions[session_id]["completed_at"] = datetime.utcnow().isoformat()
    raaga_transition_engine.stop_session()
    runtime_store.update(
        therapy_active=False,
        therapy_session_id=None,
        playlist_version=0,
        therapy_playlist=[],
        active_raaga="",
    )
    runtime_metrics_store.update_therapy_status(
        raaga_transition_engine.therapy_snapshot(
            headset_ready=runtime_metrics_store.snapshot().get("headset_ready", False)
        )
    )
    return {"status": "stopped", "session_id": session_id}
