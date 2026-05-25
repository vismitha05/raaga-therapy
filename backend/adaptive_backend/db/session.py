from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from adaptive_backend.core.config import settings


# SQLite-specific options for async support
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
    echo=False
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
