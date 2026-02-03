"""Git sync module for syncing custom sources from a git repository."""

import logging
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from bizon_platform.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class GitSyncResult:
    """Result of a git sync operation."""

    success: bool
    message: str
    commit_hash: Optional[str] = None
    files_updated: int = 0
    synced_at: Optional[datetime] = None


class GitSyncError(Exception):
    """Error during git sync operation."""

    pass


def _get_repo_url_with_auth() -> str:
    """Get the repo URL with authentication token if configured."""
    repo_url = settings.git_sync_repo_url
    if not repo_url:
        raise GitSyncError("Git sync repo URL not configured")

    # If token is provided and URL is HTTPS, inject it
    if settings.git_sync_token and repo_url.startswith("https://"):
        # Insert token into URL: https://token@github.com/...
        repo_url = repo_url.replace("https://", f"https://{settings.git_sync_token}@")

    return repo_url


def _run_git_command(cmd: list[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """Run a git command and handle errors."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
        )
        if result.returncode != 0:
            logger.error(f"Git command failed: {' '.join(cmd)}")
            logger.error(f"stderr: {result.stderr}")
            raise GitSyncError(f"Git command failed: {result.stderr.strip()}")
        return result
    except subprocess.TimeoutExpired:
        raise GitSyncError("Git command timed out")
    except FileNotFoundError:
        raise GitSyncError("Git is not installed or not in PATH")


def _get_temp_clone_dir() -> Path:
    """Get the temporary directory for cloning."""
    return Path("/tmp/bizon-git-sync-temp")


def _get_current_commit_hash(repo_dir: Path) -> Optional[str]:
    """Get the current commit hash of a repo."""
    try:
        result = _run_git_command(["git", "rev-parse", "HEAD"], cwd=repo_dir)
        return result.stdout.strip()[:8]  # Short hash
    except GitSyncError:
        return None


def _count_source_files(directory: Path) -> int:
    """Count the number of source.py files in a directory."""
    count = 0
    if directory.exists():
        for item in directory.iterdir():
            if item.is_dir() and (item / "source.py").exists():
                count += 1
    return count


def sync_from_git() -> GitSyncResult:
    """Sync custom sources from the configured git repository.

    This performs a sparse checkout of just the custom_sources directory.
    """
    if not settings.git_sync_enabled:
        return GitSyncResult(
            success=False,
            message="Git sync is not enabled",
        )

    if not settings.git_sync_repo_url:
        return GitSyncResult(
            success=False,
            message="Git sync repo URL not configured",
        )

    logger.info(f"Starting git sync from {settings.git_sync_repo_url}")

    temp_dir = _get_temp_clone_dir()
    target_dir = Path(settings.custom_sources_dir)

    try:
        # Clean up any existing temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        # Get authenticated URL
        repo_url = _get_repo_url_with_auth()

        # Clone with sparse checkout
        logger.info("Cloning repository (sparse checkout)...")

        # Initialize empty repo
        temp_dir.mkdir(parents=True)
        _run_git_command(["git", "init"], cwd=temp_dir)
        _run_git_command(["git", "remote", "add", "origin", repo_url], cwd=temp_dir)

        # Configure sparse checkout
        _run_git_command(["git", "config", "core.sparseCheckout", "true"], cwd=temp_dir)

        # Set sparse checkout paths
        sparse_file = temp_dir / ".git" / "info" / "sparse-checkout"
        sparse_file.parent.mkdir(parents=True, exist_ok=True)
        sparse_file.write_text(f"{settings.git_sync_path}/\n")

        # Fetch and checkout
        _run_git_command(
            ["git", "fetch", "--depth=1", "origin", settings.git_sync_branch],
            cwd=temp_dir,
        )
        _run_git_command(
            ["git", "checkout", settings.git_sync_branch],
            cwd=temp_dir,
        )

        # Get commit hash
        commit_hash = _get_current_commit_hash(temp_dir)

        # Copy sources to target directory
        source_dir = temp_dir / settings.git_sync_path
        if not source_dir.exists():
            raise GitSyncError(f"Path '{settings.git_sync_path}' not found in repository")

        # Ensure target directory exists
        target_dir.mkdir(parents=True, exist_ok=True)

        # Copy each source directory
        files_updated = 0
        for item in source_dir.iterdir():
            if item.is_dir() and (item / "source.py").exists():
                dest = target_dir / item.name
                # Remove existing and copy new
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
                files_updated += 1
                logger.info(f"Synced source: {item.name}")

        # Clean up temp directory
        shutil.rmtree(temp_dir)

        message = f"Synced {files_updated} source(s) from {settings.git_sync_branch}@{commit_hash}"
        logger.info(message)

        return GitSyncResult(
            success=True,
            message=message,
            commit_hash=commit_hash,
            files_updated=files_updated,
            synced_at=datetime.utcnow(),
        )

    except GitSyncError as e:
        # Clean up temp directory on error
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        logger.error(f"Git sync failed: {e}")
        return GitSyncResult(
            success=False,
            message=str(e),
        )
    except Exception as e:
        # Clean up temp directory on error
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        logger.exception("Unexpected error during git sync")
        return GitSyncResult(
            success=False,
            message=f"Unexpected error: {e}",
        )


def sync_on_startup() -> None:
    """Sync from git on application startup if enabled."""
    if not settings.git_sync_enabled:
        logger.info("Git sync is disabled")
        return

    logger.info("Git sync is enabled, syncing on startup...")
    result = sync_from_git()

    if result.success:
        logger.info(f"Startup sync complete: {result.message}")
    else:
        logger.warning(f"Startup sync failed: {result.message}")
