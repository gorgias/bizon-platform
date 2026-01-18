"""Application settings for bizon-platform-lite."""

from typing import Literal, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql+asyncpg://bizon:bizon@localhost:5432/bizon_platform_lite"

    # API
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Worker
    worker_poll_interval: int = 2  # seconds

    # Storage backend (local only for lite version)
    storage_backend: Literal["local"] = "local"
    storage_local_path: str = "/tmp/bizon-outputs"

    # Custom sources directory (local Python files)
    custom_sources_dir: str = "./custom_sources"

    # Git sync for custom sources (production deployments)
    git_sync_enabled: bool = False
    git_sync_repo_url: Optional[str] = None  # e.g., https://github.com/org/repo.git
    git_sync_branch: str = "main"
    git_sync_path: str = "custom_sources"  # subdirectory in repo to sync
    git_sync_token: Optional[str] = None  # PAT for private repos

    # Encryption (for config secrets)
    # Generate a key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    encryption_key: Optional[str] = None

    # Execution backend
    execution_backend: Literal["subprocess", "docker"] = "subprocess"

    # Docker backend settings (when execution_backend=docker)
    docker_host: Optional[str] = None
    docker_runner_image: str = "bizon-platform-lite:latest"
    docker_memory_limit: str = "2g"
    docker_cpu_limit: float = 2.0
    docker_timeout_seconds: int = 300

    # CORS
    cors_allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Instance branding (for white-label deployments)
    instance_name: str = "Bizon"
    instance_description: str = "Data pipeline orchestration platform"

    # Optional authentication (basic auth)
    # If set, all API endpoints (except /api/health) require basic auth
    admin_password: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
