"""Pytest fixtures for bizon_platform tests.

No authentication required - simplified fixture setup.
"""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from tests.fixtures.configs import VALID_DUMMY_CONFIG


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Create database tables once per session."""
    from bizon_platform.db.models import Base
    from bizon_platform.db.session import get_engine, reset_engine

    # Reset any previous engine
    reset_engine()

    engine = get_engine()
    async with engine.begin() as conn:
        # Drop all tables first to ensure clean schema
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables with the latest schema
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup after all tests
    await engine.dispose()


@pytest_asyncio.fixture
async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing the FastAPI app."""
    from bizon_platform.api.app import create_app
    from bizon_platform.db.session import get_engine

    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # Clean up data after each test
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM pipeline_runs"))
        await conn.execute(text("DELETE FROM pipelines"))
        await conn.execute(text("DELETE FROM saved_connectors"))


@pytest_asyncio.fixture
async def client_mocked(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client with mocked bizon-core for fast tests."""
    from bizon_platform.api.app import create_app
    from bizon_platform.db.session import get_engine

    # Mock RunnerFactory to skip bizon-core validation
    mock_runner = MagicMock()
    mock_runner.run.return_value = None
    mock_factory = MagicMock()
    mock_factory.create_from_config_dict.return_value = mock_runner

    with patch.dict(
        "sys.modules",
        {
            "bizon": MagicMock(),
            "bizon.engine": MagicMock(),
            "bizon.engine.engine": MagicMock(),
        },
    ):
        with patch("bizon.engine.engine.RunnerFactory", mock_factory, create=True):
            app = create_app()
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as ac:
                yield ac

    # Clean up data after each test
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM pipeline_runs"))
        await conn.execute(text("DELETE FROM pipelines"))
        await conn.execute(text("DELETE FROM saved_connectors"))


@pytest_asyncio.fixture
async def pipeline(client: AsyncClient) -> dict[str, Any]:
    """Create a test pipeline and return its data."""
    response = await client.post(
        "/api/pipelines",
        json={"name": "test-pipeline", "config": VALID_DUMMY_CONFIG},
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def pipeline_mocked(client_mocked: AsyncClient) -> dict[str, Any]:
    """Create a test pipeline with mocked bizon-core and return its data."""
    response = await client_mocked.post(
        "/api/pipelines",
        json={"name": "test-pipeline", "config": VALID_DUMMY_CONFIG},
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def pipeline_with_run(
    client: AsyncClient, pipeline: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create a pipeline with a pending run."""
    run_response = await client.post(
        f"/api/pipelines/{pipeline['id']}/run",
        json={"triggered_by": "manual"},
    )
    assert run_response.status_code == 201
    return pipeline, run_response.json()


@pytest.fixture
def mock_bizon_runner():
    """Fixture providing a mocked bizon RunnerFactory and runner."""
    mock_runner = MagicMock()
    mock_runner.run.return_value = None

    with patch("bizon.engine.engine.RunnerFactory") as mock_factory:
        mock_factory.create_from_config_dict.return_value = mock_runner
        yield {"factory": mock_factory, "runner": mock_runner}
