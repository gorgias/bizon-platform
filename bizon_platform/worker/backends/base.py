"""Base class for execution backends."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """Result of a pipeline execution."""

    success: bool
    logs: str
    error: str | None = None
    output_file: str | None = None
    output_file_size: int | None = None
    cancelled: bool = False


class ExecutionBackend(ABC):
    """Abstract base class for pipeline execution backends.

    Backends handle the actual execution of bizon pipelines.
    Different backends can run pipelines in different ways:
    - SubprocessBackend: Run in a subprocess (default)
    """

    @abstractmethod
    async def run(
        self,
        run_id: str,
        config: dict,
        check_cancelled: Callable[[], bool],
        flush_logs: Callable[[str], None],
        output_dir: str | None = None,
    ) -> ExecutionResult:
        """Execute a pipeline and return the result.

        Args:
            run_id: Unique identifier for this run
            config: Pipeline configuration dict
            check_cancelled: Callable that returns True if run was cancelled
            flush_logs: Callable(logs: str) to flush logs to DB
            output_dir: Optional directory for output files

        Returns:
            ExecutionResult with success status, logs, and any error
        """
        pass
