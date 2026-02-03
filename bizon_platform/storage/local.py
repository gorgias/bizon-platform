"""Local filesystem storage backend."""

import os
from pathlib import Path

import aiofiles
import aiofiles.os

from bizon_platform.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """Storage backend using local filesystem.

    Files are stored at {base_path}/{key}.
    """

    def __init__(self, base_path: str):
        """Initialize local storage backend.

        Args:
            base_path: Base directory for storing files
        """
        self.base_path = Path(base_path)

    def _get_full_path(self, key: str) -> Path:
        """Get the full filesystem path for a key."""
        return self.base_path / key

    async def write(self, key: str, data: bytes) -> str:
        """Write data to local filesystem."""
        full_path = self._get_full_path(key)

        # Create parent directories if needed
        await aiofiles.os.makedirs(full_path.parent, exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(data)

        return key

    async def read(self, key: str) -> bytes:
        """Read data from local filesystem."""
        full_path = self._get_full_path(key)

        if not full_path.exists():
            raise FileNotFoundError(f"Key not found: {key}")

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def exists(self, key: str) -> bool:
        """Check if file exists on local filesystem."""
        full_path = self._get_full_path(key)
        return full_path.exists()

    async def delete(self, key: str) -> None:
        """Delete file from local filesystem."""
        full_path = self._get_full_path(key)

        if not full_path.exists():
            raise FileNotFoundError(f"Key not found: {key}")

        await aiofiles.os.remove(full_path)

        # Try to remove empty parent directories
        try:
            parent = full_path.parent
            while parent != self.base_path:
                if not any(parent.iterdir()):
                    await aiofiles.os.rmdir(parent)
                    parent = parent.parent
                else:
                    break
        except OSError:
            # Directory not empty or other error, ignore
            pass

    async def get_download_url(self, key: str, expires_in: int = 3600) -> str:
        """Get the file path (local storage doesn't use URLs).

        For local storage, we return the absolute file path.
        The API layer handles serving the file content.
        """
        full_path = self._get_full_path(key)

        if not full_path.exists():
            raise FileNotFoundError(f"Key not found: {key}")

        return str(full_path.absolute())

    async def list_keys(self, prefix: str) -> list[str]:
        """List all files with given prefix."""
        prefix_path = self._get_full_path(prefix)

        if not prefix_path.exists():
            return []

        keys = []
        if prefix_path.is_dir():
            # List all files in directory
            for root, _, files in os.walk(prefix_path):
                for file in files:
                    full_path = Path(root) / file
                    # Convert to relative key
                    relative = full_path.relative_to(self.base_path)
                    keys.append(str(relative))
        elif prefix_path.is_file():
            # Single file matches
            keys.append(prefix)

        return sorted(keys)
