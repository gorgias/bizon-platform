"""Database session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bizon_platform_lite.settings import settings

# Module-level variables, initialized lazily
_engine: Optional[AsyncEngine] = None
_async_session: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """Get or create the database engine (lazy initialization)."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(settings.database_url, echo=settings.debug)
    return _engine


def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session maker (lazy initialization)."""
    global _async_session
    if _async_session is None:
        _async_session = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _async_session


def reset_engine():
    """Reset the engine and session maker (useful for testing)."""
    global _engine, _async_session
    _engine = None
    _async_session = None


# Backward compatibility properties
class _EngineProxy:
    """Proxy that provides lazy access to the engine."""

    def __getattr__(self, name):
        return getattr(get_engine(), name)


class _SessionProxy:
    """Proxy that provides lazy access to the session maker."""

    def __call__(self, *args, **kwargs):
        return get_async_session_maker()(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(get_async_session_maker(), name)


# These can be imported and used like the old globals
engine = _EngineProxy()
async_session = _SessionProxy()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
