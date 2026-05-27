from fastapi import APIRouter

from adaptive_backend.api.dependencies import monitoring_service

router = APIRouter(prefix="/eeg", tags=["eeg"])


@router.get("/live")
async def live_eeg():
    """Latest headband sample for polling when WebSocket is unavailable."""
    sample = monitoring_service.latest_sample_dict()
    if sample is None:
        return {
            "eeg_status": "waiting",
            "detected_state": "Connecting",
            "confidence": 0,
        }
    return sample


@router.get("/health")
async def eeg_health():
    listener = monitoring_service.eeg_listener
    return {
        "has_data": listener.latest is not None,
        "simulating": listener.simulating,
    }
