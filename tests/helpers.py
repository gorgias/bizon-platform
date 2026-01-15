"""Test helper functions."""

from typing import Any

from httpx import AsyncClient

from tests.fixtures.configs import (
    SAMPLE_DESTINATION_CONFIG,
    SAMPLE_SOURCE_CONFIG,
    VALID_DUMMY_CONFIG,
)

__all__ = [
    "create_pipeline",
    "create_saved_source",
    "create_saved_destination",
    "SAMPLE_SOURCE_CONFIG",
    "SAMPLE_DESTINATION_CONFIG",
    "VALID_DUMMY_CONFIG",
]


async def create_pipeline(
    client: AsyncClient,
    name: str = "test-pipeline",
    config: dict | None = None,
    schedule: str | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    """Helper to create a test pipeline."""
    payload = {
        "name": name,
        "config": config or VALID_DUMMY_CONFIG,
        "enabled": enabled,
    }
    if schedule:
        payload["schedule"] = schedule

    response = await client.post("/api/pipelines", json=payload)
    assert response.status_code == 201, f"Failed to create pipeline: {response.text}"
    return response.json()


async def create_saved_source(
    client: AsyncClient,
    name: str = "test-source",
    connector_name: str = "hubspot",
    config: dict | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Helper to create a saved source connector."""
    payload = {
        "name": name,
        "connector_name": connector_name,
        "config": config or SAMPLE_SOURCE_CONFIG,
    }
    if description:
        payload["description"] = description

    response = await client.post("/api/saved/sources", json=payload)
    assert response.status_code == 201, f"Failed to create saved source: {response.text}"
    return response.json()


async def create_saved_destination(
    client: AsyncClient,
    name: str = "test-destination",
    connector_name: str = "bigquery",
    config: dict | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Helper to create a saved destination connector."""
    payload = {
        "name": name,
        "connector_name": connector_name,
        "config": config or SAMPLE_DESTINATION_CONFIG,
    }
    if description:
        payload["description"] = description

    response = await client.post("/api/saved/destinations", json=payload)
    assert response.status_code == 201, f"Failed to create saved destination: {response.text}"
    return response.json()
