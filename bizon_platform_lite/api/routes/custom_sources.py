"""Custom sources management endpoints."""

import asyncio
import importlib.util
import os
import shutil
import zipfile
from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from bizon_platform_lite.settings import settings

router = APIRouter(prefix="/custom-sources", tags=["custom-sources"])

# Timeout for connection checks (in seconds)
CHECK_TIMEOUT_SECONDS = 30


class SourceCodeResponse(BaseModel):
    """Response containing source code."""

    name: str
    code: str
    file_path: str


class TestConnectionRequest(BaseModel):
    """Request to test a custom source connection."""

    stream: str


class TestConnectionResponse(BaseModel):
    """Response from connection test."""

    success: bool
    message: str


class UploadResponse(BaseModel):
    """Response from uploading a source."""

    name: str
    file_path: str
    streams: list[str]
    message: str


class DeleteResponse(BaseModel):
    """Response from deleting a source."""

    message: str


def _get_source_class(source_name: str):
    """Load and return the source class from a custom source."""
    from bizon.source.source import AbstractSource

    source_dir = os.path.join(settings.custom_sources_dir, source_name)
    source_file = os.path.join(source_dir, "source.py")

    if not os.path.exists(source_file):
        raise HTTPException(status_code=404, detail=f"Custom source '{source_name}' not found")

    spec = importlib.util.spec_from_file_location(f"custom_source_{source_name}", source_file)
    if spec is None or spec.loader is None:
        raise HTTPException(status_code=500, detail=f"Failed to load source module for '{source_name}'")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Find the source class
    source_class = None
    for name, obj in vars(module).items():
        if isinstance(obj, type) and issubclass(obj, AbstractSource) and obj != AbstractSource:
            source_class = obj
            break

    if source_class is None:
        raise HTTPException(status_code=500, detail=f"No valid source class found in '{source_name}'")

    return source_class


@router.get("/{name}/code", response_model=SourceCodeResponse)
async def get_source_code(name: str) -> SourceCodeResponse:
    """Get the source code for a custom source."""
    source_dir = os.path.join(settings.custom_sources_dir, name)
    source_file = os.path.join(source_dir, "source.py")

    if not os.path.exists(source_file):
        raise HTTPException(status_code=404, detail=f"Custom source '{name}' not found")

    try:
        with open(source_file, "r", encoding="utf-8") as f:
            code = f.read()

        docker_path = f"/custom_sources/{name}/source.py"

        return SourceCodeResponse(
            name=name,
            code=code,
            file_path=docker_path,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read source code: {str(e)}")


def _test_connection_sync(source_name: str, stream: str) -> TestConnectionResponse:
    """Synchronous connection test implementation."""
    try:
        source_class = _get_source_class(source_name)
        config_class = source_class.get_config_class()

        # Check if stream is valid
        available_streams = source_class.streams()
        if stream not in available_streams:
            return TestConnectionResponse(
                success=False,
                message=f"Stream '{stream}' not found. Available: {', '.join(available_streams)}",
            )

        # Create config and source instance
        docker_path = f"/custom_sources/{source_name}/source.py"
        config = config_class(name=source_name, stream=stream, source_file_path=docker_path)
        source_instance = source_class(config=config)

        # Test connection
        success, error_message = source_instance.check_connection()

        if success:
            return TestConnectionResponse(success=True, message="Connection successful")
        else:
            return TestConnectionResponse(
                success=False,
                message=error_message or "Connection check failed",
            )

    except HTTPException:
        raise
    except Exception as e:
        return TestConnectionResponse(success=False, message=f"Test failed: {str(e)}")


@router.post("/{name}/test", response_model=TestConnectionResponse)
async def test_connection(name: str, request: TestConnectionRequest) -> TestConnectionResponse:
    """Test connection for a custom source stream."""
    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, _test_connection_sync, name, request.stream),
            timeout=CHECK_TIMEOUT_SECONDS,
        )
        return result
    except asyncio.TimeoutError:
        return TestConnectionResponse(
            success=False,
            message=f"Connection check timed out after {CHECK_TIMEOUT_SECONDS} seconds",
        )
    except HTTPException:
        raise
    except Exception as e:
        return TestConnectionResponse(success=False, message=f"Test failed: {str(e)}")


@router.post("/upload", response_model=UploadResponse)
async def upload_source(file: UploadFile = File(...)) -> UploadResponse:
    """Upload a new custom source.

    Accepts either:
    - A .py file (will create a directory named after the file)
    - A .zip file containing a directory with source.py
    """
    from bizon.source.source import AbstractSource

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()

    # Ensure custom sources directory exists
    os.makedirs(settings.custom_sources_dir, exist_ok=True)

    if file.filename.endswith(".py"):
        # Single Python file upload
        source_name = file.filename.replace(".py", "").replace("-", "_").lower()
        source_dir = os.path.join(settings.custom_sources_dir, source_name)

        if os.path.exists(source_dir):
            raise HTTPException(status_code=400, detail=f"Source '{source_name}' already exists")

        os.makedirs(source_dir)
        source_file = os.path.join(source_dir, "source.py")

        try:
            with open(source_file, "wb") as f:
                f.write(content)
        except Exception as e:
            shutil.rmtree(source_dir, ignore_errors=True)
            raise HTTPException(status_code=500, detail=f"Failed to write source file: {str(e)}")

    elif file.filename.endswith(".zip"):
        # Zip file upload
        try:
            with zipfile.ZipFile(BytesIO(content)) as zf:
                # Find the source.py file
                source_py_path = None
                for name in zf.namelist():
                    if name.endswith("source.py") and not name.startswith("__"):
                        source_py_path = name
                        break

                if not source_py_path:
                    raise HTTPException(status_code=400, detail="No source.py found in zip file")

                # Determine source name from path
                parts = source_py_path.split("/")
                if len(parts) > 1:
                    source_name = parts[0].replace("-", "_").lower()
                else:
                    source_name = file.filename.replace(".zip", "").replace("-", "_").lower()

                source_dir = os.path.join(settings.custom_sources_dir, source_name)

                if os.path.exists(source_dir):
                    raise HTTPException(status_code=400, detail=f"Source '{source_name}' already exists")

                os.makedirs(source_dir)

                # Extract source.py
                source_file = os.path.join(source_dir, "source.py")
                with zf.open(source_py_path) as src, open(source_file, "wb") as dst:
                    dst.write(src.read())

        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid zip file")
        except HTTPException:
            raise
        except Exception as e:
            if "source_dir" in locals():
                shutil.rmtree(source_dir, ignore_errors=True)
            raise HTTPException(status_code=500, detail=f"Failed to extract zip: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="File must be .py or .zip")

    # Validate the uploaded source
    try:
        source_file_path = os.path.join(source_dir, "source.py")
        spec = importlib.util.spec_from_file_location(f"custom_source_{source_name}", source_file_path)
        if spec is None or spec.loader is None:
            raise Exception("Failed to load module spec")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find the source class
        source_class = None
        for attr_name, obj in vars(module).items():
            if isinstance(obj, type) and issubclass(obj, AbstractSource) and obj != AbstractSource:
                source_class = obj
                break

        if source_class is None:
            raise Exception("No valid source class found (must inherit from AbstractSource)")

        streams = source_class.streams()

    except Exception as e:
        shutil.rmtree(source_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=f"Invalid source: {str(e)}")

    docker_path = f"/custom_sources/{source_name}/source.py"

    return UploadResponse(
        name=source_name,
        file_path=docker_path,
        streams=streams,
        message=f"Successfully uploaded source '{source_name}'",
    )


@router.delete("/{name}", response_model=DeleteResponse)
async def delete_source(name: str) -> DeleteResponse:
    """Delete a custom source."""
    source_dir = os.path.join(settings.custom_sources_dir, name)

    if not os.path.exists(source_dir):
        raise HTTPException(status_code=404, detail=f"Custom source '{name}' not found")

    try:
        shutil.rmtree(source_dir)
        return DeleteResponse(message=f"Successfully deleted source '{name}'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete source: {str(e)}")
