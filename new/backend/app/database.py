from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Alias used by Celery tasks that need a session outside a request context
async_session_factory = AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
