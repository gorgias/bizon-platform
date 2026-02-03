"""Platform statistics endpoint."""

from fastapi import APIRouter
from sqlalchemy import func, select

from bizon_platform.api.schemas import StatsResponse
from bizon_platform.db.models import Pipeline, PipelineRun
from bizon_platform.db.session import get_session

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    """Get platform statistics."""
    async with get_session() as session:
        # Total pipelines
        total_result = await session.execute(select(func.count(Pipeline.id)))
        total_pipelines = total_result.scalar() or 0

        # Enabled pipelines
        enabled_result = await session.execute(
            select(func.count(Pipeline.id)).where(Pipeline.enabled == True)  # noqa: E712
        )
        enabled_pipelines = enabled_result.scalar() or 0

        # Total runs
        total_runs_result = await session.execute(select(func.count(PipelineRun.id)))
        total_runs = total_runs_result.scalar() or 0

        # Successful runs
        success_result = await session.execute(
            select(func.count(PipelineRun.id)).where(PipelineRun.status == "success")
        )
        successful_runs = success_result.scalar() or 0

        # Failed runs
        failed_result = await session.execute(
            select(func.count(PipelineRun.id)).where(PipelineRun.status == "failed")
        )
        failed_runs = failed_result.scalar() or 0

        # Pending runs
        pending_result = await session.execute(
            select(func.count(PipelineRun.id)).where(PipelineRun.status == "pending")
        )
        pending_runs = pending_result.scalar() or 0

        return StatsResponse(
            total_pipelines=total_pipelines,
            enabled_pipelines=enabled_pipelines,
            total_runs=total_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            pending_runs=pending_runs,
        )
