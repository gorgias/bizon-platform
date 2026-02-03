"""Log file storage utilities for pipeline runs.

Logs are stored as plain text files at:
    /tmp/bizon-outputs/logs/{pipeline_id}/{run_id}.log

This module provides:
- Sync write operations for worker callbacks (run in threads)
- Async read operations for API endpoints
- Offset-based reading for log streaming
"""

import asyncio
from pathlib import Path
from typing import Optional
from uuid import UUID

from bizon_platform.settings import settings


def get_logs_base_dir() -> Path:
    """Get the base directory for log files."""
    return Path(settings.storage_local_path) / "logs"


def get_log_file_path(pipeline_id: UUID | str, run_id: UUID | str) -> Path:
    """Get the path to a log file for a specific pipeline run.

    Args:
        pipeline_id: The pipeline UUID
        run_id: The run UUID

    Returns:
        Path to the log file: /tmp/bizon-outputs/logs/{pipeline_id}/{run_id}.log
    """
    return get_logs_base_dir() / str(pipeline_id) / f"{run_id}.log"


def append_logs_sync(pipeline_id: UUID | str, run_id: UUID | str, content: str) -> str:
    """Append log content to a file (synchronous for worker callback).

    Creates the parent directory if it doesn't exist.

    Args:
        pipeline_id: The pipeline UUID
        run_id: The run UUID
        content: The full log content to write (replaces existing content)

    Returns:
        The relative path to the log file for storing in DB
    """
    log_path = get_log_file_path(pipeline_id, run_id)

    # Ensure parent directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Write full content (replacing previous content)
    # This matches the existing behavior where flush_logs receives all logs
    log_path.write_text(content, encoding="utf-8")

    # Return relative path for DB storage
    return f"logs/{pipeline_id}/{run_id}.log"


async def read_logs(pipeline_id: UUID | str, run_id: UUID | str, offset: int = 0) -> tuple[str, int]:
    """Read logs from a file starting at an offset (async for API).

    Args:
        pipeline_id: The pipeline UUID
        run_id: The run UUID
        offset: Byte offset to start reading from (default 0 for full content)

    Returns:
        Tuple of (content from offset, new offset position)
    """
    log_path = get_log_file_path(pipeline_id, run_id)

    if not log_path.exists():
        return "", 0

    # Run file I/O in thread pool to avoid blocking
    def _read_from_offset() -> tuple[str, int]:
        with open(log_path, "r", encoding="utf-8") as f:
            f.seek(offset)
            content = f.read()
            new_offset = f.tell()
        return content, new_offset

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _read_from_offset)


async def read_full_logs(pipeline_id: UUID | str, run_id: UUID | str) -> Optional[str]:
    """Read the full log content for a run.

    Args:
        pipeline_id: The pipeline UUID
        run_id: The run UUID

    Returns:
        Full log content or None if file doesn't exist
    """
    log_path = get_log_file_path(pipeline_id, run_id)

    if not log_path.exists():
        return None

    def _read_file() -> str:
        return log_path.read_text(encoding="utf-8")

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _read_file)


def delete_logs_sync(pipeline_id: UUID | str, run_id: UUID | str) -> bool:
    """Delete log file for a run (synchronous).

    Args:
        pipeline_id: The pipeline UUID
        run_id: The run UUID

    Returns:
        True if file was deleted, False if it didn't exist
    """
    log_path = get_log_file_path(pipeline_id, run_id)

    if log_path.exists():
        log_path.unlink()
        # Clean up empty parent directory
        try:
            log_path.parent.rmdir()
        except OSError:
            pass  # Directory not empty or doesn't exist
        return True
    return False
