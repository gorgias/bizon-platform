"""Connector discovery endpoints - list available sources and destinations."""

import asyncio
import os
from typing import Any

import yaml
from fastapi import APIRouter
from pydantic import BaseModel

from bizon_platform.api.schemas import (
    CheckResponse,
    DestinationCheckRequest,
    SourceCheckRequest,
)
from bizon_platform.api.validators import validate_config_security

router = APIRouter(prefix="/connectors", tags=["connectors"])

# Timeout for connection checks (in seconds)
CHECK_TIMEOUT_SECONDS = 30


class StreamInfo(BaseModel):
    """Information about a source stream."""

    name: str
    supports_incremental: bool


class SourceInfo(BaseModel):
    """Information about an available source."""

    name: str
    streams: list[StreamInfo]
    config_examples: list[dict[str, Any]]


class DestinationInfo(BaseModel):
    """Information about an available destination."""

    name: str
    config_examples: list[dict[str, Any]]


class CustomSourceInfo(BaseModel):
    """Information about a custom source."""

    name: str
    file_path: str
    streams: list[str]


def find_example_files(connector_path: str) -> list[dict[str, Any]]:
    """Find and parse all *.example.yml files in a connector's config directory."""
    config_dir = os.path.join(connector_path, "config")
    examples: list[dict[str, Any]] = []

    if not os.path.exists(config_dir):
        return examples

    for filename in sorted(os.listdir(config_dir)):
        if filename.endswith(".example.yml") or filename.endswith(".example.yaml"):
            filepath = os.path.join(config_dir, filename)
            try:
                with open(filepath) as f:
                    content = yaml.safe_load(f)
                    if content:
                        examples.append(content)
            except Exception as e:
                print(f"Warning: Failed to parse {filepath}: {e}")

    return examples


def get_bizon_connectors_path() -> str:
    """Get the path to bizon connectors directory."""
    try:
        from bizon.utils import BIZON_ABSOLUTE_PATH

        return os.path.join(BIZON_ABSOLUTE_PATH, "connectors")
    except ImportError:
        return ""


@router.get("/sources", response_model=list[SourceInfo])
async def list_sources() -> list[SourceInfo]:
    """List all available source connectors with their example configs."""
    try:
        from bizon.source.discover import discover_all_sources

        sources = discover_all_sources()
        connectors_path = get_bizon_connectors_path()
        result = []

        for source_name, source_model in sources.items():
            source_path = os.path.join(connectors_path, "sources", source_name)
            examples = find_example_files(source_path)

            streams = [
                StreamInfo(
                    name=stream.name,
                    supports_incremental=stream.supports_incremental,
                )
                for stream in source_model.streams
            ]
            result.append(
                SourceInfo(
                    name=source_name,
                    streams=streams,
                    config_examples=examples,
                )
            )

        return sorted(result, key=lambda x: x.name)

    except Exception as e:
        print(f"Warning: Failed to discover sources: {e}")
        return []


@router.get("/destinations", response_model=list[DestinationInfo])
async def list_destinations() -> list[DestinationInfo]:
    """List all available destination connectors with their example configs."""
    try:
        from bizon.destination.config import DestinationTypes

        connectors_path = get_bizon_connectors_path()
        result = []

        for dest_type in DestinationTypes:
            dest_name = dest_type.value
            dest_path = os.path.join(connectors_path, "destinations", dest_name)
            examples = find_example_files(dest_path)

            result.append(
                DestinationInfo(
                    name=dest_name,
                    config_examples=examples,
                )
            )

        return sorted(result, key=lambda x: x.name)

    except Exception as e:
        print(f"Warning: Failed to get destinations: {e}")
        return []


@router.get("/custom-sources", response_model=list[CustomSourceInfo])
async def list_custom_sources() -> list[CustomSourceInfo]:
    """List all custom sources from the custom-sources directory."""
    import importlib.util

    from bizon.source.source import AbstractSource

    from bizon_platform.settings import settings

    custom_sources_dir = settings.custom_sources_dir
    result = []

    if not os.path.exists(custom_sources_dir):
        return result

    for item in sorted(os.listdir(custom_sources_dir)):
        item_path = os.path.join(custom_sources_dir, item)

        # Skip non-directories and special files
        if not os.path.isdir(item_path) or item.startswith(".") or item.startswith("_"):
            continue

        source_file = os.path.join(item_path, "source.py")
        if not os.path.exists(source_file):
            continue

        # Try to load the source module and find the source class
        try:
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(f"custom_source_{item}", source_file)
            if spec is None or spec.loader is None:
                continue

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the source class that inherits from AbstractSource
            source_class = None
            for name, obj in vars(module).items():
                if isinstance(obj, type) and issubclass(obj, AbstractSource) and obj != AbstractSource:
                    source_class = obj
                    break

            if source_class is None:
                continue

            streams = source_class.streams()

            # Build the file path as it should be referenced in Docker
            docker_path = f"/custom_sources/{item}/source.py"

            result.append(
                CustomSourceInfo(
                    name=item,
                    file_path=docker_path,
                    streams=streams,
                )
            )
        except Exception as e:
            print(f"Warning: Failed to load custom source {item}: {e}")
            continue

    return result


def _check_source_sync(request: SourceCheckRequest) -> CheckResponse:
    """Synchronous source check implementation (runs in thread pool)."""
    try:
        from bizon.source.discover import discover_all_sources

        source_config: dict[str, Any] = {
            "name": request.source_name,
            "stream": request.stream_name,
        }
        if request.authentication:
            source_config["authentication"] = request.authentication

        validation_result = validate_config_security(source_config)
        if not validation_result.valid:
            error_messages = [e.message for e in validation_result.errors]
            return CheckResponse(
                success=False,
                message=f"Security validation failed: {'; '.join(error_messages)}",
            )

        sources = discover_all_sources()
        if request.source_name not in sources:
            return CheckResponse(
                success=False,
                message=f"Source '{request.source_name}' not found. Available: {', '.join(sources.keys())}",
            )

        source_model = sources[request.source_name]

        try:
            stream = source_model.get_stream_by_name(request.stream_name)
        except ValueError:
            available = ", ".join(source_model.available_streams)
            return CheckResponse(
                success=False,
                message=f"Stream '{request.stream_name}' not found for "
                f"source '{request.source_name}'. Available: {available}",
            )

        source_class = stream.source_class
        config_class = source_class.get_config_class()

        config_dict: dict[str, Any] = {
            "name": request.source_name,
            "stream": request.stream_name,
        }
        if request.authentication:
            config_dict["authentication"] = request.authentication

        config_parsed = config_class(**config_dict)
        source_instance = source_class(config=config_parsed)
        success, error_message = source_instance.check_connection()

        if success:
            return CheckResponse(success=True, message="Connection successful")
        else:
            return CheckResponse(
                success=False,
                message=error_message or "Connection check failed",
            )

    except Exception as e:
        return CheckResponse(success=False, message=f"Check failed: {str(e)}")


@router.post("/sources/check", response_model=CheckResponse)
async def check_source(request: SourceCheckRequest) -> CheckResponse:
    """Check source connectivity by instantiating and testing the connection."""
    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, _check_source_sync, request),
            timeout=CHECK_TIMEOUT_SECONDS,
        )
        return result
    except asyncio.TimeoutError:
        return CheckResponse(
            success=False,
            message=f"Connection check timed out after {CHECK_TIMEOUT_SECONDS} seconds",
        )
    except Exception as e:
        return CheckResponse(success=False, message=f"Check failed: {str(e)}")


def _check_destination_sync(request: DestinationCheckRequest) -> CheckResponse:
    """Synchronous destination check implementation (runs in thread pool)."""
    try:
        from bizon.destination.config import DestinationTypes

        dest_config = {"destination": {"name": request.destination_name, "config": request.config}}
        validation_result = validate_config_security(dest_config)
        if not validation_result.valid:
            error_messages = [e.message for e in validation_result.errors]
            return CheckResponse(
                success=False,
                message=f"Security validation failed: {'; '.join(error_messages)}",
            )

        dest_names = [d.value for d in DestinationTypes]
        if request.destination_name not in dest_names:
            return CheckResponse(
                success=False,
                message=f"Destination '{request.destination_name}' not found. Available: {', '.join(dest_names)}",
            )

        from bizon.destination.destination import DestinationFactory

        if request.destination_name == "logger":
            from bizon.connectors.destinations.logger.src.config import LoggerDestinationConfig

            dest_details_config = LoggerDestinationConfig(**request.config)
        elif request.destination_name == "bigquery":
            from bizon.connectors.destinations.bigquery.src.config import BigQueryConfigDetails

            dest_details_config = BigQueryConfigDetails(**request.config)
        elif request.destination_name == "bigquery_streaming":
            from bizon.connectors.destinations.bigquery_streaming.src.config import BigQueryStreamingConfigDetails

            dest_details_config = BigQueryStreamingConfigDetails(**request.config)
        elif request.destination_name == "bigquery_streaming_v2":
            from bizon.connectors.destinations.bigquery_streaming_v2.src.config import BigQueryStreamingV2ConfigDetails

            dest_details_config = BigQueryStreamingV2ConfigDetails(**request.config)
        elif request.destination_name == "file":
            from bizon.connectors.destinations.file.src.config import FileDestinationDetailsConfig

            dest_details_config = FileDestinationDetailsConfig(**request.config)
        else:
            return CheckResponse(
                success=False,
                message=f"Destination '{request.destination_name}' config class not found",
            )

        from bizon.destination.config import AbstractDestinationConfig, DestinationTypes

        dest_config_obj = AbstractDestinationConfig(
            name=DestinationTypes(request.destination_name),
            alias=request.destination_name,
            config=dest_details_config,
        )

        from bizon.common.models import SyncMetadata
        from bizon.source.config import SourceSyncModes

        mock_sync_metadata = SyncMetadata(
            job_id="check-connection",
            name="connection-check",
            source_name="check",
            stream_name="check",
            destination_name=request.destination_name,
            destination_alias=request.destination_name,
            sync_mode=SourceSyncModes.FULL_REFRESH,
        )

        class MockBackend:
            def get_cursor_state(self):
                return None

            def create_destination_cursor(self, **kwargs):
                pass

            def update_stream_job_status(self, **kwargs):
                pass

        class MockSourceCallback:
            pass

        class MockMonitor:
            pass

        destination_instance = DestinationFactory.get_destination(
            sync_metadata=mock_sync_metadata,
            config=dest_config_obj,
            backend=MockBackend(),
            source_callback=MockSourceCallback(),
            monitor=MockMonitor(),
        )

        success = destination_instance.check_connection()

        if success:
            return CheckResponse(success=True, message="Connection successful")
        else:
            return CheckResponse(success=False, message="Connection check failed")

    except Exception as e:
        return CheckResponse(success=False, message=f"Check failed: {str(e)}")


@router.post("/destinations/check", response_model=CheckResponse)
async def check_destination(request: DestinationCheckRequest) -> CheckResponse:
    """Check destination connectivity by instantiating and testing the connection."""
    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, _check_destination_sync, request),
            timeout=CHECK_TIMEOUT_SECONDS,
        )
        return result
    except asyncio.TimeoutError:
        return CheckResponse(
            success=False,
            message=f"Connection check timed out after {CHECK_TIMEOUT_SECONDS} seconds",
        )
    except Exception as e:
        return CheckResponse(success=False, message=f"Check failed: {str(e)}")
