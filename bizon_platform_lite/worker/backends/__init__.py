"""Execution backends for pipeline runs."""

from bizon_platform_lite.worker.backends.base import ExecutionBackend, ExecutionResult
from bizon_platform_lite.worker.backends.subprocess import SubprocessBackend

__all__ = ["ExecutionBackend", "ExecutionResult", "SubprocessBackend"]


def get_backend() -> ExecutionBackend:
    """Get the configured execution backend.

    Returns SubprocessBackend by default.
    """
    from bizon_platform_lite.settings import settings

    if settings.execution_backend == "docker":
        # Docker backend not included in lite version for simplicity
        raise ValueError("Docker backend is not available in bizon-platform-lite")
    return SubprocessBackend()
