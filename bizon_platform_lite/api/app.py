"""FastAPI application factory for bizon-platform-lite."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bizon_platform_lite.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - start scheduler and git sync on startup."""
    from bizon_platform_lite.git_sync import sync_on_startup
    from bizon_platform_lite.scheduler import shutdown_scheduler, start_scheduler

    # Sync custom sources from git if enabled
    sync_on_startup()

    start_scheduler()
    yield
    shutdown_scheduler()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    from bizon_platform_lite.api.auth import optional_auth

    # Build dependencies list
    dependencies = []
    if settings.admin_password:
        from fastapi import Depends

        dependencies.append(Depends(optional_auth))

    app = FastAPI(
        title=settings.instance_name,
        description=settings.instance_description,
        version="0.1.0",
        lifespan=lifespan,
        dependencies=dependencies,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    from bizon_platform_lite.api.routes import (
        connectors,
        custom_sources,
        health,
        pipelines,
        saved_connectors,
        stats,
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(stats.router, prefix="/api")
    app.include_router(pipelines.router, prefix="/api")
    app.include_router(connectors.router, prefix="/api")
    app.include_router(custom_sources.router, prefix="/api")
    app.include_router(saved_connectors.router, prefix="/api")

    return app


# Create the app instance
app = create_app()
