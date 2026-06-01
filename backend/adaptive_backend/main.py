import asyncio

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adaptive_backend.api.dependencies import monitoring_service
from adaptive_backend.api.router import api_router
from adaptive_backend.core.config import settings
from adaptive_backend.db.init_db import init_models
from adaptive_backend.eeg.device_manager import device_manager


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_models()

    monitoring_task = asyncio.create_task(monitoring_service.start())
    capsule_task = asyncio.create_task(asyncio.to_thread(device_manager.start))

    try:
        yield
    finally:
        monitoring_service.stop()
        monitoring_task.cancel()

        device_manager.stop()
        capsule_task.cancel()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
cors_origins = [origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health():
    return {"ok": True, "service": settings.app_name}
