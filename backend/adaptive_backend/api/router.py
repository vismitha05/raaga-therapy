from fastapi import APIRouter

from adaptive_backend.api.routes.sessions import router as session_router
from adaptive_backend.api.routes.state import router as state_router
from adaptive_backend.api.routes.ws import router as ws_router
from adaptive_backend.api.routes.therapy import router as therapy_router

api_router = APIRouter()
api_router.include_router(session_router)
api_router.include_router(state_router)
api_router.include_router(ws_router)
api_router.include_router(therapy_router)
