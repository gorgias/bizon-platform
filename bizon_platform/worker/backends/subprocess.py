"""Subprocess execution backend."""

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path

from bizon_platform.storage import get_storage
from bizon_platform.worker.backends.base import ExecutionBackend, ExecutionResult

# Pattern to detect errors in logs (bizon-core uses loguru format)
ERROR_LOG_PATTERN = re.compile(r"\|\s*ERROR\s*\|")


def detect_errors_in_logs(logs: str) -> str | None:
    """Detect error messages in logs and return the first error found."""
    for line in logs.split("\n"):
        if ERROR_LOG_PATTERN.search(line):
            # Extract the error message after the log prefix
            # Format: "timestamp | LEVEL | module:line - message"
            parts = line.split(" - ", 1)
            if len(parts) > 1:
                return parts[1].strip()
            return line.strip()
    return None


class SubprocessBackend(ExecutionBackend):
    """Execute pipelines in subprocesses.

    This backend runs each pipeline in a separate Python subprocess,
    allowing for true cancellation via SIGTERM/SIGKILL.
    """

    def __init__(self):
        self._processes: dict[str, subprocess.Popen] = {}

    async def run(
        self,
        run_id: str,
        config: dict,
        check_cancelled: Callable[[], bool],
        flush_logs: Callable[[str], None],
        output_dir: str | None = None,
    ) -> ExecutionResult:
        """Execute pipeline in subprocess."""

        # Start subprocess with unbuffered output
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"  # Disable Python output buffering
        if output_dir:
            env["BIZON_OUTPUT_DIR"] = output_dir

        process = subprocess.Popen(
            [
                sys.executable,
                "-u",
                "-m",
                "bizon_platform.worker.runner",
            ],  # -u for unbuffered
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            env=env,
        )
        self._processes[run_id] = process

        # Send config via stdin
        try:
            if process.stdin is not None:
                process.stdin.write(json.dumps(config))
                process.stdin.close()
        except BrokenPipeError:
            pass

        # Use a list to accumulate logs (mutable for thread access)
        logs_buffer = []
        stop_reading = threading.Event()

        def read_stderr():
            """Read stderr in a thread to avoid blocking."""
            try:
                for line in process.stderr:
                    if stop_reading.is_set():
                        break
                    logs_buffer.append(line)
            except Exception:
                pass

        # Start reader thread
        reader_thread = threading.Thread(target=read_stderr, daemon=True)
        reader_thread.start()

        last_flush = time.time()
        cancelled = False

        try:
            # Main loop: flush logs, check cancellation
            while process.poll() is None:
                # Flush logs to DB every 2 seconds
                now = time.time()
                if now - last_flush >= 2 and logs_buffer:
                    accumulated = "".join(logs_buffer)
                    flush_logs(accumulated)
                    last_flush = now

                # Check for cancellation
                if check_cancelled():
                    cancelled = True
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=2)
                    logs_buffer.append("\n--- Cancelled by user ---\n")
                    break

                # Small sleep to avoid busy loop
                await asyncio.sleep(0.2)

            # Wait for reader thread to finish
            stop_reading.set()
            reader_thread.join(timeout=2)

            # Get final accumulated logs
            accumulated_logs = "".join(logs_buffer)

            # Final log flush
            if accumulated_logs:
                flush_logs(accumulated_logs)

            # Determine result
            if cancelled:
                return ExecutionResult(
                    success=False,
                    logs=accumulated_logs,
                    error="Cancelled by user",
                    cancelled=True,
                )

            # Check for output files and upload to storage
            output_file = None
            output_file_size = None
            if output_dir:
                output_path = Path(output_dir)
                if output_path.exists():
                    # Look for data files (json, jsonl, csv, parquet)
                    data_files: list[Path] = []
                    for pattern in ["*.json", "*.jsonl", "*.csv", "*.parquet"]:
                        data_files.extend(output_path.glob(pattern))
                    if data_files:
                        local_file = data_files[0]
                        output_file_size = local_file.stat().st_size

                        # Upload to storage backend
                        storage = get_storage()
                        # PATCH: Rename .json to .jsonl since bizon-core writes NDJSON
                        filename = local_file.name
                        if filename.endswith(".json"):
                            filename = filename[:-5] + ".jsonl"
                        storage_key = f"{run_id}/{filename}"
                        with open(local_file, "rb") as f:
                            file_data = f.read()
                        await storage.write(storage_key, file_data)
                        output_file = storage_key

                # Clean up local temp directory
                try:
                    shutil.rmtree(output_dir)
                except Exception:
                    pass

            if process.returncode == 0:
                # Even with exit code 0, check if logs contain errors
                # bizon-core may log errors but still exit successfully
                log_error = detect_errors_in_logs(accumulated_logs)
                if log_error:
                    return ExecutionResult(
                        success=False,
                        logs=accumulated_logs,
                        error=f"Pipeline completed but had errors: {log_error}",
                        output_file=output_file,
                        output_file_size=output_file_size,
                    )
                return ExecutionResult(
                    success=True,
                    logs=accumulated_logs,
                    output_file=output_file,
                    output_file_size=output_file_size,
                )
            else:
                return ExecutionResult(
                    success=False,
                    logs=accumulated_logs,
                    error=f"Process exited with code {process.returncode}",
                )

        finally:
            # Cleanup
            if run_id in self._processes:
                del self._processes[run_id]

            # Ensure process is terminated
            if process.poll() is None:
                process.kill()
                process.wait()
