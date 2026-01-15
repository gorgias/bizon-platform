"""Health check endpoint."""

from fastapi import APIRouter
from sqlalchemy import text

from bizon_platform_lite.api.schemas import HealthResponse
from bizon_platform_lite.db.session import async_session

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check API and database health."""
    db_status = "ok"
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        database=db_status,
    )
