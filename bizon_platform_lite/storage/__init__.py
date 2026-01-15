"""Storage backend abstraction for pipeline outputs."""

from functools import lru_cache

from bizon_platform_lite.storage.base import StorageBackend

__all__ = ["StorageBackend", "get_storage"]


@lru_cache
def get_storage() -> StorageBackend:
    """Get the configured storage backend singleton.

    For lite version, only local storage is supported.
    """
    from bizon_platform_lite.settings import settings
    from bizon_platform_lite.storage.local import LocalStorageBackend

    return LocalStorageBackend(base_path=settings.storage_local_path)
