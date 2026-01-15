"""Worker that polls Postgres for pending pipeline runs and executes them."""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import create_engine, select, text, update

from bizon_platform_lite.db.models import Pipeline, PipelineRun
from bizon_platform_lite.db.session import async_session
from bizon_platform_lite.settings import settings
from bizon_platform_lite.worker.backends import get_backend


def parse_database_url(url: str) -> dict:
    """Parse DATABASE_URL into components for bizon engine config."""
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    parsed = urlparse(url)

    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/") or "bizon",
        "username": parsed.username or "bizon",
        "password": parsed.password or "",
        "schema": "public",
    }


def build_engine_config(sync_cursor_every: int = 100) -> dict:
    """Build the bizon engine config using the platform's Postgres database.

    Args:
        sync_cursor_every: Number of iterations before syncing cursor to DB. Default: 100.
    """
    db_config = parse_database_url(settings.database_url)

    return {
        "backend": {
            "type": "postgres",
            "config": {
                "host": db_config["host"],
                "port": db_config["port"],
                "database": db_config["database"],
                "schema": db_config["schema"],
                "username": db_config["username"],
                "password": db_config["password"],
            },
            "syncCursorInDBEvery": sync_cursor_every,
        },
    }


def inject_engine_config(config: dict) -> dict:
    """Inject the platform's engine config into the pipeline config.

    Merges user-provided engine settings (like syncCursorInDBEvery) with platform defaults.
    """
    config = config.copy()

    # Extract user-provided engine settings
    user_engine = config.pop("engine", {})
    sync_cursor_every = user_engine.get("syncCursorInDBEvery", 100)

    # Build engine config with user settings
    config["engine"] = build_engine_config(sync_cursor_every=sync_cursor_every)
    return config


def is_file_destination(config: dict) -> bool:
    """Check if the pipeline uses the file destination."""
    return config.get("destination", {}).get("name") == "file"


# Initialize execution backend based on settings
backend = get_backend()

# Sync DB engine for callbacks
_sync_engine = None


def get_sync_engine():
    """Get or create sync database engine."""
    global _sync_engine
    if _sync_engine is None:
        sync_url = settings.database_url.replace("+asyncpg", "")
        _sync_engine = create_engine(sync_url)
    return _sync_engine


async def claim_next_job() -> tuple[PipelineRun, dict] | None:
    """Atomically claim the next pending job using SELECT FOR UPDATE SKIP LOCKED."""
    async with async_session() as session:
        result = await session.execute(
            select(PipelineRun)
            .where(PipelineRun.status == "pending")
            .order_by(PipelineRun.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        run = result.scalar_one_or_none()
        if not run:
            return None

        run.status = "running"
        run.started_at = datetime.utcnow()
        await session.commit()

        pipeline = await session.get(Pipeline, run.pipeline_id)
        if not pipeline:
            run.status = "failed"
            run.error = "Pipeline not found"
            run.finished_at = datetime.utcnow()
            await session.commit()
            return None

        return run, pipeline.config


async def execute_pipeline(run_id, config: dict) -> None:
    """Execute a bizon pipeline using the configured backend."""
    engine = get_sync_engine()
    run_id_str = str(run_id)

    # Inject engine config
    config = inject_engine_config(config)

    # Determine output directory for file destinations
    output_dir = None
    if is_file_destination(config):
        output_dir = str(Path(tempfile.gettempdir()) / "bizon-outputs" / run_id_str)

    # Callbacks for the backend
    def check_cancelled() -> bool:
        """Check if run was cancelled in DB."""
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT status FROM pipeline_runs WHERE id = :id"),
                    {"id": run_id_str},
                )
                row = result.fetchone()
                return row and row[0] == "cancelled"
        except Exception:
            return False

    def flush_logs(logs: str) -> None:
        """Flush logs to DB."""
        try:
            with engine.connect() as conn:
                conn.execute(
                    text("UPDATE pipeline_runs SET logs = :logs WHERE id = :id AND status = 'running'"),
                    {"logs": logs, "id": run_id_str},
                )
                conn.commit()
        except Exception as e:
            print(f"[WARN] Failed to flush logs: {e}")

    try:
        # Execute via backend
        result = await backend.run(
            run_id=run_id_str,
            config=config,
            check_cancelled=check_cancelled,
            flush_logs=flush_logs,
            output_dir=output_dir,
        )

        # Update database based on result
        if result.cancelled:
            # Already marked as cancelled in DB, just update logs
            async with async_session() as session:
                await session.execute(
                    update(PipelineRun).where(PipelineRun.id == run_id).values(logs=result.logs or None)
                )
                await session.commit()
            print(f"[CANCELLED] Run {run_id} was cancelled")

        elif result.success:
            async with async_session() as session:
                row_result = await session.execute(
                    update(PipelineRun)
                    .where(PipelineRun.id == run_id)
                    .where(PipelineRun.status == "running")
                    .values(
                        status="success",
                        finished_at=datetime.utcnow(),
                        logs=result.logs or None,
                        output_file=result.output_file,
                        output_file_size=result.output_file_size,
                    )
                )
                await session.commit()
                if row_result.rowcount == 0:
                    print(f"[SKIP] Run {run_id} status already changed")
                else:
                    print(f"[OK] Run {run_id} completed successfully")

        else:
            async with async_session() as session:
                row_result = await session.execute(
                    update(PipelineRun)
                    .where(PipelineRun.id == run_id)
                    .where(PipelineRun.status == "running")
                    .values(
                        status="failed",
                        finished_at=datetime.utcnow(),
                        error=result.error,
                        logs=result.logs or None,
                    )
                )
                await session.commit()
                if row_result.rowcount == 0:
                    print(f"[SKIP] Run {run_id} status already changed")
                else:
                    print(f"[FAILED] Run {run_id}: {result.error}")

    except Exception as e:
        print(f"[ERROR] Execute pipeline error: {e}")
        async with async_session() as session:
            await session.execute(
                update(PipelineRun)
                .where(PipelineRun.id == run_id)
                .where(PipelineRun.status == "running")
                .values(
                    status="failed",
                    finished_at=datetime.utcnow(),
                    error=str(e),
                )
            )
            await session.commit()


async def worker_loop() -> None:
    """Main worker loop - polls for jobs and executes them."""
    print(f"Worker started, polling every {settings.worker_poll_interval}s...")
    db_display = settings.database_url.split("@")[1] if "@" in settings.database_url else settings.database_url
    print(f"Using database: {db_display}")
    print(f"Using backend: {backend.__class__.__name__}")

    while True:
        try:
            job = await claim_next_job()
            if job:
                run, config = job
                print(f"[START] Executing run {run.id}")
                await execute_pipeline(run.id, config)
            else:
                await asyncio.sleep(settings.worker_poll_interval)
        except Exception as e:
            print(f"[ERROR] Worker error: {e}")
            await asyncio.sleep(settings.worker_poll_interval)


def main() -> None:
    """Entry point for the worker."""
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()
