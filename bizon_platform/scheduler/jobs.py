"""Scheduled jobs for pipeline execution."""

from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from croniter import croniter
from sqlalchemy import select

from bizon_platform.db.models import Pipeline, PipelineRun
from bizon_platform.db.session import async_session

scheduler = AsyncIOScheduler()


def should_run_now(cron_expression: str) -> bool:
    """Check if a cron expression should trigger now (within the last minute)."""
    try:
        cron = croniter(cron_expression, datetime.utcnow())
        prev_run = cron.get_prev(datetime)
        # If the previous scheduled time was within the last 60 seconds, trigger
        return (datetime.utcnow() - prev_run).total_seconds() < 60
    except Exception:
        return False


async def check_scheduled_pipelines() -> None:
    """Check for pipelines that should run based on their schedule."""
    async with async_session() as session:
        # Get all enabled pipelines with a schedule
        result = await session.execute(
            select(Pipeline).where(
                Pipeline.enabled == True,  # noqa: E712
                Pipeline.schedule.isnot(None),
            )
        )
        pipelines = result.scalars().all()

        for pipeline in pipelines:
            if should_run_now(pipeline.schedule):
                # Check if there's already a pending/running job for this pipeline
                existing = await session.execute(
                    select(PipelineRun).where(
                        PipelineRun.pipeline_id == pipeline.id,
                        PipelineRun.status.in_(["pending", "running"]),
                    )
                )
                if existing.scalar_one_or_none():
                    continue  # Skip if already running/pending

                # Create a new run
                run = PipelineRun(
                    pipeline_id=pipeline.id,
                    status="pending",
                    triggered_by="schedule",
                )
                session.add(run)
                print(f"[SCHEDULE] Created run for pipeline '{pipeline.name}'")

        await session.commit()


def start_scheduler() -> None:
    """Start the scheduler."""
    scheduler.add_job(
        check_scheduled_pipelines,
        trigger="interval",
        minutes=1,
        id="check_scheduled_pipelines",
        replace_existing=True,
    )
    scheduler.start()
    print("Scheduler started")


def shutdown_scheduler() -> None:
    """Stop the scheduler."""
    scheduler.shutdown()
