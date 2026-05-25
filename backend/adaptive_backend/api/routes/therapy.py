"""
therapy_routes.py
---------------
API endpoints for the complete Raga Therapy workflow:
1. EEG monitoring (15-second scan)
2. State selection (user chooses target state)
3. Duration selection (user chooses session length)
4. Playlist generation and playback
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, BackgroundTasks
from pydantic import BaseModel

from adaptive_backend.domain.enums import BrainState, DayPart
from adaptive_backend.services.eeg_monitoring_service import (
    EEGMonitoringService, EEGSimulator
)
from adaptive_backend.services.raga_therapy_engine import (
    RagaTherapyEngine, EEGStateAnalyzer, FrequencyBand,
    TransitionValidator, EEGDetection, TherapyPlaylist, RagaTrack
)

# ─── Setup ────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/therapy", tags=["therapy"])

# Global monitoring service (one per session ideally, but simplified here)
monitoring_service = EEGMonitoringService(window_seconds=15)

# Session storage (in production, use a database)
active_sessions: dict[str, dict] = {}


# ─── Request/Response Models ──────────────────────────────────────────────────

class EEGScanRequest(BaseModel):
    """Request to start EEG monitoring"""
    duration_seconds: int = 15
    simulate: bool = False  # Use simulated EEG for testing


class EEGScanResponse(BaseModel):
    """Response after EEG scan completes"""
    session_id: str
    detected_band: str  # FrequencyBand enum
    detected_state: str  # BrainState enum
    confidence: float
    alpha_power: float
    beta_power: float
    theta_power: float
    monitoring_duration_seconds: int


class StateSelectionRequest(BaseModel):
    """User selects target therapeutic state"""
    session_id: str
    target_state: str  # "sleep", "relaxed", "focused"


class DurationSelectionRequest(BaseModel):
    """User selects session duration"""
    session_id: str
    duration_minutes: int  # 10, 20, or 30


class PlaylistResponse(BaseModel):
    """Generated therapy playlist"""
    session_id: str
    start_band: str
    target_state: str
    total_duration_minutes: int
    total_steps: int
    day_part: str
    tracks: list[dict]  # Serialized RagaTracks


class MonitoringProgressResponse(BaseModel):
    """Current EEG monitoring progress"""
    progress_percent: float
    time_remaining_seconds: float
    is_monitoring: bool


class TrackProgressUpdate(BaseModel):
    """Update on current playing track"""
    session_id: str
    track_index: int
    raga_name: str
    frequency_range: tuple[float, float]
    duration_seconds: float
    elapsed_seconds: float
    is_playing: bool


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/eeg-scan/start", response_model=dict)
async def start_eeg_scan(request: EEGScanRequest, background_tasks: BackgroundTasks):
    """
    Start 15-second EEG monitoring scan.

    Process:
    1. Initialize session
    2. Start background monitoring thread
    3. Return session_id to client
    4. Client polls /eeg-scan/progress until complete

    Returns:
        session_id: Unique identifier for this therapy session
    """
    session_id = str(uuid.uuid4())

    # Create session state
    active_sessions[session_id] = {
        "created_at": datetime.utcnow(),
        "eeg_detection": None,
        "target_state": None,
        "duration_minutes": None,
        "playlist": None,
        "playback_progress": {},
    }

    # Start monitoring in background
    monitoring_service.window_seconds = request.duration_seconds

    if request.simulate:
        # Use simulated EEG for testing
        background_tasks.add_task(
            _run_simulated_eeg_scan, session_id, request.duration_seconds
        )
    else:
        # Use real EEG hardware
        background_tasks.add_task(
            _run_real_eeg_scan, session_id, request.duration_seconds
        )

    return {
        "session_id": session_id,
        "message": "EEG scan started, monitoring for 15 seconds",
        "total_duration_seconds": request.duration_seconds,
    }


@router.get("/eeg-scan/progress/{session_id}", response_model=MonitoringProgressResponse)
async def get_scan_progress(session_id: str):
    """
    Poll current EEG scan progress.

    Frontend calls this repeatedly (every 1-2 seconds) until progress reaches 100%.

    Returns:
        progress_percent: 0.0 - 100.0
        time_remaining_seconds: Seconds left in scan
        is_monitoring: Whether still active
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    progress = monitoring_service.get_monitoring_progress()
    time_remaining = monitoring_service.get_monitoring_time_remaining()

    return MonitoringProgressResponse(
        progress_percent=progress * 100,
        time_remaining_seconds=time_remaining,
        is_monitoring=monitoring_service._monitoring,
    )


@router.get("/eeg-scan/result/{session_id}", response_model=EEGScanResponse)
async def get_scan_result(session_id: str):
    """
    Get final EEG scan results after monitoring completes.

    Called after frontend detects progress == 100%.

    Returns:
        detected_band: T1, T2, A1, A2, B1, or B2
        detected_state: "sleep", "relaxed", or "focused"
        confidence: 0.0 - 1.0 confidence score
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]

    if session["eeg_detection"] is None:
        # Still monitoring or no detection yet
        return HTTPException(status_code=202, detail="Still monitoring...")

    detection: EEGDetection = session["eeg_detection"]

    return EEGScanResponse(
        session_id=session_id,
        detected_band=detection.detected_band.value,
        detected_state=detection.detected_state.value,
        confidence=detection.confidence,
        alpha_power=detection.alpha_power,
        beta_power=detection.beta_power,
        theta_power=detection.theta_power,
        monitoring_duration_seconds=15,
    )


@router.post("/state-selection", response_model=dict)
async def select_target_state(request: StateSelectionRequest):
    """
    User selects desired therapeutic state (sleep, relaxed, focused).

    Args:
        session_id: From EEG scan
        target_state: "sleep", "relaxed", or "focused"

    Returns:
        Confirmation and estimated durations for each option
    """
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[request.session_id]

    # Validate state selection
    try:
        target_state = BrainState(request.target_state)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target state: {request.target_state}"
        )

    # Store selection
    session["target_state"] = target_state

    # Get EEG detection
    detection = session["eeg_detection"]
    if not detection:
        raise HTTPException(status_code=400, detail="No EEG detection available")

    # Estimate effectiveness for each duration
    estimates = RagaTherapyEngine.estimate_session_duration(
        detection.detected_band, target_state
    )

    return {
        "session_id": request.session_id,
        "target_state": target_state.value,
        "current_state": detection.detected_state.value,
        "current_band": detection.detected_band.value,
        "effectiveness_estimates": estimates,
        "message": "Target state selected. Choose session duration.",
    }


@router.post("/duration-selection", response_model=PlaylistResponse)
async def select_duration(request: DurationSelectionRequest):
    """
    User selects session duration (10, 20, or 30 minutes).
    Generates complete therapy playlist.

    Args:
        session_id: From previous steps
        duration_minutes: 10, 20, or 30

    Returns:
        Complete playlist with raga sequence and timings
    """
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[request.session_id]

    # Validate inputs
    if request.duration_minutes not in [10, 20, 30]:
        raise HTTPException(
            status_code=400,
            detail="Duration must be 10, 20, or 30 minutes"
        )

    detection: EEGDetection = session["eeg_detection"]
    target_state: BrainState = session["target_state"]

    if not detection or not target_state:
        raise HTTPException(
            status_code=400,
            detail="Missing EEG detection or target state"
        )

    # Validate transition safety
    is_valid, reason = TransitionValidator.validate_transition(
        detection.detected_band,
        target_state,
        request.duration_minutes,
    )

    if not is_valid:
        raise HTTPException(status_code=400, detail=reason)

    # Generate playlist
    playlist = RagaTherapyEngine.generate_therapy_playlist(
        session_id=request.session_id,
        detected_band=detection.detected_band,
        target_state=target_state,
        duration_minutes=request.duration_minutes,
    )

    # Store in session
    session["playlist"] = playlist
    session["duration_minutes"] = request.duration_minutes

    # Serialize tracks
    track_dicts = [
        {
            "order": track.order_in_sequence,
            "band": track.band.value,
            "raga": track.raga_name,
            "duration_seconds": track.duration_seconds,
            "frequency_range": track.frequency_range_hz,
            "estimated_start_time_seconds": sum(
                t.duration_seconds for t in playlist.tracks[:track.order_in_sequence]
            ),
        }
        for track in playlist.tracks
    ]

    return PlaylistResponse(
        session_id=request.session_id,
        start_band=playlist.start_band.value,
        target_state=playlist.target_state.value,
        total_duration_minutes=playlist.total_duration_minutes,
        total_steps=playlist.total_transition_steps,
        day_part=playlist.day_part.value,
        tracks=track_dicts,
    )


@router.get("/playlist/{session_id}", response_model=PlaylistResponse)
async def get_playlist(session_id: str):
    """Retrieve generated playlist (may be called multiple times during playback)"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]

    if not session["playlist"]:
        raise HTTPException(status_code=404, detail="No playlist generated yet")

    playlist: TherapyPlaylist = session["playlist"]

    # Serialize tracks
    track_dicts = [
        {
            "order": track.order_in_sequence,
            "band": track.band.value,
            "raga": track.raga_name,
            "duration_seconds": track.duration_seconds,
            "frequency_range": track.frequency_range_hz,
            "estimated_start_time_seconds": sum(
                t.duration_seconds for t in playlist.tracks[:track.order_in_sequence]
            ),
        }
        for track in playlist.tracks
    ]

    return PlaylistResponse(
        session_id=session_id,
        start_band=playlist.start_band.value,
        target_state=playlist.target_state.value,
        total_duration_minutes=playlist.total_duration_minutes,
        total_steps=playlist.total_transition_steps,
        day_part=playlist.day_part.value,
        tracks=track_dicts,
    )


@router.post("/playback/update")
async def update_playback_progress(update: TrackProgressUpdate):
    """Track playback progress (optional, for logging/analytics)"""
    if update.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[update.session_id]
    session["playback_progress"] = {
        "track_index": update.track_index,
        "raga": update.raga_name,
        "elapsed_seconds": update.elapsed_seconds,
        "timestamp": datetime.utcnow(),
    }

    return {
        "status": "progress_recorded",
        "session_id": update.session_id,
    }


@router.post("/session/complete/{session_id}")
async def complete_session(session_id: str):
    """Mark session as complete and clean up resources"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]
    session["completed_at"] = datetime.utcnow()

    return {
        "status": "session_completed",
        "session_id": session_id,
        "duration": (session["completed_at"] - session["created_at"]).total_seconds(),
    }


# ─── Background Tasks ────────────────────────────────────────────────────────

async def _run_simulated_eeg_scan(session_id: str, duration_seconds: int):
    """Simulate a realistic 15-second EEG scan"""
    if session_id not in active_sessions:
        return

    # Randomly select a brain state pattern
    import random
    state_choice = random.choice([
        EEGSimulator.generate_relaxed_pattern,
        EEGSimulator.generate_focused_pattern,
        EEGSimulator.generate_sleepy_pattern,
    ])

    patterns = state_choice(duration_seconds)

    monitoring_service.start_monitoring()

    for alpha, beta, theta in patterns:
        monitoring_service.add_power_bands(alpha, beta, theta)
        import time
        time.sleep(1.0)

    detection = monitoring_service.stop_monitoring()
    active_sessions[session_id]["eeg_detection"] = detection


async def _run_real_eeg_scan(session_id: str, duration_seconds: int):
    """Run real EEG hardware scan"""
    if session_id not in active_sessions:
        return

    # TODO: Connect to actual EEG hardware (Neury Capsule, Muse, etc.)
    # For now, use simulated data
    import time
    import random

    monitoring_service.start_monitoring()
    monitoring_service.window_seconds = duration_seconds

    # Simulate receiving EEG data
    for i in range(duration_seconds):
        alpha = random.uniform(0.3, 0.7)
        beta = random.uniform(0.2, 0.6)
        theta = random.uniform(0.1, 0.5)

        monitoring_service.add_power_bands(alpha, beta, theta)
        time.sleep(1.0)

    detection = monitoring_service.stop_monitoring()
    active_sessions[session_id]["eeg_detection"] = detection
