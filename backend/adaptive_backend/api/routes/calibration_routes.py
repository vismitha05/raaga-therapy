from fastapi import APIRouter

router = APIRouter(prefix="/calibration", tags=["calibration"])


@router.get("/status")
async def calibration_status():
    return {"status": "not_started", "message": "Calibration service scaffold ready."}

