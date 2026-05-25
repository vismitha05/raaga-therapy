from adaptive_backend.db.base import Base
from adaptive_backend.db.session import engine
from adaptive_backend.domain.models import models  # noqa: F401


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
