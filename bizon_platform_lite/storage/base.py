"""Abstract base class for storage backends."""

from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """Abstract storage backend for pipeline outputs.

    All methods are async to support both local and cloud storage backends.
    Keys are paths relative to the storage root (e.g., "run-id/output.json").
    """

    @abstractmethod
    async def write(self, key: str, data: bytes) -> str:
        """Write data to storage.

        Args:
            key: Storage key/path (e.g., "run-id/output.json")
            data: Binary data to write

        Returns:
            The storage key where data was written
        """
        pass

    @abstractmethod
    async def read(self, key: str) -> bytes:
        """Read data from storage.

        Args:
            key: Storage key/path

        Returns:
            Binary data

        Raises:
            FileNotFoundError: If key does not exist
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in storage.

        Args:
            key: Storage key/path

        Returns:
            True if key exists, False otherwise
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete data from storage.

        Args:
            key: Storage key/path

        Raises:
            FileNotFoundError: If key does not exist
        """
        pass

    @abstractmethod
    async def get_download_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a URL for downloading the data.

        For local storage, returns the file path.
        For cloud storage, returns a signed URL.

        Args:
            key: Storage key/path
            expires_in: URL expiration time in seconds (for cloud storage)

        Returns:
            Download URL or file path
        """
        pass

    @abstractmethod
    async def list_keys(self, prefix: str) -> list[str]:
        """List all keys with a given prefix.

        Args:
            prefix: Key prefix to filter by (e.g., "run-id/")

        Returns:
            List of matching keys
        """
        pass
