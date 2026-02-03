"""Pipeline CRUD and run endpoints - No Auth Version."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from croniter import croniter
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from bizon_platform.api.schemas import (
    PipelineCreate,
    PipelineResponse,
    PipelineRunCreate,
    PipelineRunResponse,
    PipelineUpdate,
    RunLogsResponse,
)
from bizon_platform.api.validators import validate_config_security
from bizon_platform.db.models import Pipeline, PipelineRun
from bizon_platform.db.session import get_session
from bizon_platform.settings import settings
from bizon_platform.storage.logs import read_full_logs

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


def validate_schedule(schedule: Optional[str]) -> None:
    """Validate cron schedule syntax.

    Raises HTTPException with 400 status if schedule is invalid.
    """
    if not schedule:
        return
    try:
        croniter(schedule)
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid cron schedule '{schedule}': {str(e)}",
        )


def validate_bizon_config(config: dict[str, Any]) -> None:
    """Validate bizon config by attempting to create a runner.

    Also validates for security issues:
    - Transform code injection (blocks dangerous Python patterns)
    - YAML injection patterns (blocks !!python/object, etc.)

    Raises HTTPException with 400 status if config is invalid.
    """
    # Validate security first (transforms + YAML injection)
    result = validate_config_security(config)
    if not result.valid:
        errors = "; ".join(e.message for e in result.errors)
        raise HTTPException(
            status_code=400,
            detail=f"Security validation failed: {errors}",
        )

    # Then validate with bizon-core
    try:
        from bizon.engine.engine import RunnerFactory

        RunnerFactory.create_from_config_dict(config)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pipeline configuration: {e}",
        )


@router.post("", response_model=PipelineResponse, status_code=201)
async def create_pipeline(data: PipelineCreate) -> Pipeline:
    """Create a new pipeline."""
    validate_schedule(data.schedule)
    validate_bizon_config(data.config)

    async with get_session() as session:
        pipeline = Pipeline(
            name=data.name,
            config=data.config,
            schedule=data.schedule,
            enabled=data.enabled,
            tags=data.tags or [],
        )
        session.add(pipeline)
        await session.flush()
        await session.refresh(pipeline)
        return pipeline


@router.get("", response_model=list[PipelineResponse])
async def list_pipelines(
    limit: int = 100,
    offset: int = 0,
    enabled: Optional[bool] = None,
    tags: Optional[str] = None,
) -> list[Pipeline]:
    """List all pipelines.

    Args:
        tags: Comma-separated list of tags to filter by (pipelines must have ALL specified tags)
    """
    async with get_session() as session:
        query = (
            select(Pipeline)
            .limit(limit)
            .offset(offset)
            .order_by(Pipeline.created_at.desc())
        )
        if enabled is not None:
            query = query.where(Pipeline.enabled == enabled)
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            for tag in tag_list:
                query = query.where(Pipeline.tags.contains([tag]))
        result = await session.execute(query)
        return list(result.scalars().all())


@router.get("/tags", response_model=list[str])
async def list_all_tags() -> list[str]:
    """Get all unique tags used across pipelines."""
    async with get_session() as session:
        result = await session.execute(select(Pipeline.tags))
        all_tags = set()
        for (tags,) in result:
            if tags:
                all_tags.update(tags)
        return sorted(all_tags)


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(pipeline_id: uuid.UUID) -> Pipeline:
    """Get a pipeline by ID."""
    async with get_session() as session:
        pipeline = await session.get(Pipeline, pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        return pipeline


@router.put("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(pipeline_id: uuid.UUID, data: PipelineUpdate) -> Pipeline:
    """Update a pipeline."""
    if data.schedule is not None:
        validate_schedule(data.schedule)
    if data.config is not None:
        validate_bizon_config(data.config)

    async with get_session() as session:
        pipeline = await session.get(Pipeline, pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(pipeline, key, value)

        await session.flush()
        await session.refresh(pipeline)
        return pipeline


@router.delete("/{pipeline_id}", status_code=204)
async def delete_pipeline(pipeline_id: uuid.UUID) -> None:
    """Delete a pipeline."""
    async with get_session() as session:
        pipeline = await session.get(Pipeline, pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        await session.delete(pipeline)


@router.post("/{pipeline_id}/duplicate", response_model=PipelineResponse, status_code=201)
async def duplicate_pipeline(pipeline_id: uuid.UUID) -> Pipeline:
    """Duplicate an existing pipeline."""
    async with get_session() as session:
        original = await session.get(Pipeline, pipeline_id)
        if not original:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        # Generate unique name
        base_name = original.name
        copy_num = 1
        new_name = f"{base_name} (copy)"

        while True:
            existing = await session.execute(
                select(Pipeline).where(Pipeline.name == new_name)
            )
            if not existing.scalar_one_or_none():
                break
            copy_num += 1
            new_name = f"{base_name} (copy {copy_num})"

        duplicate = Pipeline(
            name=new_name,
            config=original.config,
            schedule=original.schedule,
            enabled=False,  # Start disabled for safety
            tags=original.tags or [],
        )
        session.add(duplicate)
        await session.flush()
        await session.refresh(duplicate)
        return duplicate


@router.post("/{pipeline_id}/sync-streams", response_model=list[PipelineResponse], status_code=201)
async def sync_other_streams(pipeline_id: uuid.UUID) -> list[Pipeline]:
    """Create pipelines for all other streams of the same source.

    Uses the same config as the source pipeline, creates one pipeline
    per stream that doesn't already have a pipeline for that source+stream combo.
    """
    async with get_session() as session:
        original = await session.get(Pipeline, pipeline_id)
        if not original:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        source_config = original.config.get("source", {})
        source_name = source_config.get("name")
        current_stream = source_config.get("stream")
        source_file_path = source_config.get("source_file_path")

        if not source_name or not current_stream:
            raise HTTPException(
                status_code=400,
                detail="Pipeline source configuration is incomplete",
            )

        # Get all available streams for this source
        all_streams: list[str] = []

        if source_file_path:
            # Custom source - load dynamically to get streams
            import importlib.util
            import os

            from bizon.source.source import AbstractSource

            from bizon_platform.settings import settings

            # Convert docker path to local path
            local_path = source_file_path.replace("/custom_sources/", "")
            full_path = os.path.join(settings.custom_sources_dir, local_path)

            if os.path.exists(full_path):
                try:
                    spec = importlib.util.spec_from_file_location("custom_source", full_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        for _, obj in vars(module).items():
                            if isinstance(obj, type) and issubclass(obj, AbstractSource) and obj != AbstractSource:
                                all_streams = obj.streams()
                                break
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to load custom source: {e}",
                    )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Custom source file not found: {source_file_path}",
                )
        else:
            # Built-in source - use bizon discovery
            try:
                from bizon.source.discover import discover_all_sources

                sources = discover_all_sources()
                if source_name in sources:
                    all_streams = [s.name for s in sources[source_name].streams]
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Source '{source_name}' not found",
                    )
            except ImportError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to discover sources: {e}",
                )

        # Get existing pipelines for this source to avoid duplicates
        existing_result = await session.execute(select(Pipeline))
        existing_pipelines = existing_result.scalars().all()

        existing_streams = set()
        for p in existing_pipelines:
            p_source = p.config.get("source", {})
            if p_source.get("name") == source_name:
                existing_streams.add(p_source.get("stream"))

        # Filter to streams that don't have pipelines yet
        streams_to_create = [s for s in all_streams if s not in existing_streams]

        if not streams_to_create:
            return []  # All streams already have pipelines

        # Create pipelines for remaining streams
        created_pipelines = []
        base_name = original.name

        for stream in streams_to_create:
            # Generate unique name
            new_name = f"{base_name}-{stream}"
            suffix = 2
            while True:
                existing = await session.execute(
                    select(Pipeline).where(Pipeline.name == new_name)
                )
                if not existing.scalar_one_or_none():
                    break
                new_name = f"{base_name}-{stream}-{suffix}"
                suffix += 1

            # Clone config with new stream
            new_config = dict(original.config)
            new_config["source"] = dict(source_config)
            new_config["source"]["stream"] = stream

            new_pipeline = Pipeline(
                name=new_name,
                config=new_config,
                schedule=original.schedule,
                enabled=original.enabled,
                tags=original.tags or [],
            )
            session.add(new_pipeline)
            created_pipelines.append(new_pipeline)

        await session.flush()
        for p in created_pipelines:
            await session.refresh(p)

        return created_pipelines


@router.post("/{pipeline_id}/run", response_model=PipelineRunResponse, status_code=201)
async def trigger_run(
    pipeline_id: uuid.UUID,
    data: PipelineRunCreate = PipelineRunCreate(),
) -> PipelineRun:
    """Trigger a pipeline run.

    Returns 409 Conflict if a run is already pending or running for this pipeline.
    """
    async with get_session() as session:
        pipeline = await session.get(Pipeline, pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        # Check if there's already a pending/running run
        existing_run = await session.execute(
            select(PipelineRun).where(
                PipelineRun.pipeline_id == pipeline_id,
                PipelineRun.status.in_(["pending", "running"]),
            )
        )
        if existing_run.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A run is already pending or running for this pipeline",
            )

        run = PipelineRun(
            pipeline_id=pipeline_id,
            status="pending",
            triggered_by=data.triggered_by,
        )
        session.add(run)
        await session.flush()
        await session.refresh(run)
        return run


@router.get("/{pipeline_id}/runs", response_model=list[PipelineRunResponse])
async def list_runs(pipeline_id: uuid.UUID, limit: int = 50) -> list[PipelineRun]:
    """List runs for a pipeline."""
    async with get_session() as session:
        pipeline = await session.get(Pipeline, pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        query = (
            select(PipelineRun)
            .where(PipelineRun.pipeline_id == pipeline_id)
            .order_by(PipelineRun.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())


@router.get("/runs/{run_id}", response_model=PipelineRunResponse)
async def get_run(run_id: uuid.UUID) -> PipelineRun:
    """Get a run by ID."""
    async with get_session() as session:
        run = await session.get(PipelineRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return run


@router.get("/runs/{run_id}/logs", response_model=RunLogsResponse)
async def get_run_logs(run_id: uuid.UUID) -> RunLogsResponse:
    """Get logs for a run.

    Reads logs from file if available (new runs), falls back to DB column (legacy runs).
    """
    async with get_session() as session:
        run = await session.get(PipelineRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        # Try file-based logs first (new runs)
        if run.log_file_path:
            logs = await read_full_logs(run.pipeline_id, run_id)
            if logs is not None:
                return RunLogsResponse(logs=logs)

        # Fall back to DB logs (legacy runs or file not found)
        return RunLogsResponse(logs=run.logs)


@router.post("/runs/{run_id}/cancel", response_model=PipelineRunResponse)
async def cancel_run(run_id: uuid.UUID) -> PipelineRun:
    """Cancel a pipeline run.

    - Pending runs are cancelled immediately
    - Running runs are marked as cancelled
    - Already finished runs return an error
    """
    async with get_session() as session:
        run = await session.get(PipelineRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        if run.status in ("success", "failed", "cancelled"):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel run with status '{run.status}'",
            )

        run.status = "cancelled"
        run.finished_at = datetime.utcnow()
        run.error = "Cancelled by user"

        await session.flush()
        await session.refresh(run)
        return run


@router.get("/runs/{run_id}/download", response_model=None)
async def download_run_output(run_id: uuid.UUID):
    """Download the output file from a pipeline run.

    Only available for runs that:
    - Used the 'file' destination
    - Completed successfully
    - Have an output file recorded
    """
    async with get_session() as session:
        run = await session.get(PipelineRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        if not run.output_file:
            raise HTTPException(
                status_code=404,
                detail="No output file available for this run",
            )

        # For lite version, we only support local storage
        file_path = Path(settings.storage_local_path) / run.output_file
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Output file not found in storage",
            )

        # Detect media type from file extension
        extension = file_path.suffix.lower()
        media_types = {
            ".json": "application/json",
            ".jsonl": "application/x-ndjson",
            ".csv": "text/csv",
            ".parquet": "application/octet-stream",
        }
        media_type = media_types.get(extension, "application/octet-stream")

        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type=media_type,
        )
