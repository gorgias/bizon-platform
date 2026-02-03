"""Tests for saved connectors CRUD operations."""

import uuid

from httpx import AsyncClient

from tests.helpers import (
    SAMPLE_DESTINATION_CONFIG,
    SAMPLE_SOURCE_CONFIG,
    create_saved_destination,
    create_saved_source,
)

# =============================================================================
# Saved Sources Tests
# =============================================================================


class TestCreateSavedSource:
    """Tests for POST /api/saved/sources."""

    async def test_create_saved_source_success(self, client_mocked: AsyncClient):
        """Create a valid saved source."""
        data = await create_saved_source(client_mocked, name="my-hubspot")
        assert data["name"] == "my-hubspot"
        assert data["type"] == "source"
        assert data["connector_name"] == "hubspot"
        assert data["config"] == SAMPLE_SOURCE_CONFIG
        assert data["description"] is None
        assert "id" in data
        assert "created_at" in data

    async def test_create_saved_source_with_description(
        self, client_mocked: AsyncClient
    ):
        """Create saved source with description."""
        data = await create_saved_source(
            client_mocked,
            name="prod-hubspot",
            description="Production HubSpot connection",
        )
        assert data["description"] == "Production HubSpot connection"

    async def test_create_saved_source_duplicate_name(
        self, client_mocked: AsyncClient
    ):
        """Reject duplicate source name."""
        await create_saved_source(client_mocked, name="duplicate-name")

        # Try to create another with same name
        response = await client_mocked.post(
            "/api/saved/sources",
            json={
                "name": "duplicate-name",
                "connector_name": "shopify",
                "config": SAMPLE_SOURCE_CONFIG,
            },
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    async def test_same_name_allowed_for_source_and_destination(
        self, client_mocked: AsyncClient
    ):
        """Same name can be used for source and destination."""
        source = await create_saved_source(client_mocked, name="shared-name")
        dest = await create_saved_destination(client_mocked, name="shared-name")
        assert source["name"] == dest["name"]
        assert source["type"] == "source"
        assert dest["type"] == "destination"


class TestListSavedSources:
    """Tests for GET /api/saved/sources."""

    async def test_list_saved_sources_empty(self, client_mocked: AsyncClient):
        """List returns empty when no sources saved."""
        response = await client_mocked.get("/api/saved/sources")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_saved_sources_multiple(self, client_mocked: AsyncClient):
        """List returns all saved sources."""
        for i in range(3):
            await create_saved_source(client_mocked, name=f"source-{i}")

        response = await client_mocked.get("/api/saved/sources")
        assert response.status_code == 200
        assert len(response.json()) == 3

    async def test_list_saved_sources_excludes_destinations(
        self, client_mocked: AsyncClient
    ):
        """List sources does not include destinations."""
        await create_saved_source(client_mocked, name="my-source")
        await create_saved_destination(client_mocked, name="my-destination")

        response = await client_mocked.get("/api/saved/sources")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "my-source"

    async def test_list_saved_sources_pagination(self, client_mocked: AsyncClient):
        """List respects pagination parameters."""
        for i in range(5):
            await create_saved_source(client_mocked, name=f"source-{i}")

        response = await client_mocked.get("/api/saved/sources?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestGetSavedSource:
    """Tests for GET /api/saved/sources/{id}."""

    async def test_get_saved_source_success(self, client_mocked: AsyncClient):
        """Get existing saved source by ID."""
        source = await create_saved_source(client_mocked, name="test-source")

        response = await client_mocked.get(f"/api/saved/sources/{source['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == source["id"]
        assert response.json()["name"] == "test-source"

    async def test_get_saved_source_not_found(self, client_mocked: AsyncClient):
        """Get non-existent source returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client_mocked.get(f"/api/saved/sources/{fake_id}")
        assert response.status_code == 404

    async def test_get_source_returns_404_for_destination(
        self, client_mocked: AsyncClient
    ):
        """Getting a destination ID via sources endpoint returns 404."""
        dest = await create_saved_destination(client_mocked, name="test-dest")

        response = await client_mocked.get(f"/api/saved/sources/{dest['id']}")
        assert response.status_code == 404


class TestUpdateSavedSource:
    """Tests for PUT /api/saved/sources/{id}."""

    async def test_update_saved_source_name(self, client_mocked: AsyncClient):
        """Update saved source name."""
        source = await create_saved_source(client_mocked, name="old-name")

        response = await client_mocked.put(
            f"/api/saved/sources/{source['id']}",
            json={"name": "new-name"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "new-name"

    async def test_update_saved_source_config(self, client_mocked: AsyncClient):
        """Update saved source config."""
        source = await create_saved_source(client_mocked, name="test-source")

        new_config = {**SAMPLE_SOURCE_CONFIG, "stream": "companies"}
        response = await client_mocked.put(
            f"/api/saved/sources/{source['id']}",
            json={"config": new_config},
        )
        assert response.status_code == 200
        assert response.json()["config"]["stream"] == "companies"

    async def test_update_saved_source_description(self, client_mocked: AsyncClient):
        """Update saved source description."""
        source = await create_saved_source(client_mocked, name="test-source")

        response = await client_mocked.put(
            f"/api/saved/sources/{source['id']}",
            json={"description": "Updated description"},
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"

    async def test_update_saved_source_not_found(self, client_mocked: AsyncClient):
        """Update non-existent source returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client_mocked.put(
            f"/api/saved/sources/{fake_id}",
            json={"name": "new-name"},
        )
        assert response.status_code == 404


class TestDeleteSavedSource:
    """Tests for DELETE /api/saved/sources/{id}."""

    async def test_delete_saved_source_success(self, client_mocked: AsyncClient):
        """Delete existing saved source."""
        source = await create_saved_source(client_mocked, name="to-delete")

        response = await client_mocked.delete(f"/api/saved/sources/{source['id']}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = await client_mocked.get(f"/api/saved/sources/{source['id']}")
        assert get_response.status_code == 404

    async def test_delete_saved_source_not_found(self, client_mocked: AsyncClient):
        """Delete non-existent source returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client_mocked.delete(f"/api/saved/sources/{fake_id}")
        assert response.status_code == 404


# =============================================================================
# Saved Destinations Tests
# =============================================================================


class TestCreateSavedDestination:
    """Tests for POST /api/saved/destinations."""

    async def test_create_saved_destination_success(self, client_mocked: AsyncClient):
        """Create a valid saved destination."""
        data = await create_saved_destination(client_mocked, name="my-bigquery")
        assert data["name"] == "my-bigquery"
        assert data["type"] == "destination"
        assert data["connector_name"] == "bigquery"
        assert data["config"] == SAMPLE_DESTINATION_CONFIG

    async def test_create_saved_destination_duplicate_name(
        self, client_mocked: AsyncClient
    ):
        """Reject duplicate destination name."""
        await create_saved_destination(client_mocked, name="duplicate")

        response = await client_mocked.post(
            "/api/saved/destinations",
            json={
                "name": "duplicate",
                "connector_name": "snowflake",
                "config": SAMPLE_DESTINATION_CONFIG,
            },
        )
        assert response.status_code == 409


class TestListSavedDestinations:
    """Tests for GET /api/saved/destinations."""

    async def test_list_saved_destinations_empty(self, client_mocked: AsyncClient):
        """List returns empty when no destinations saved."""
        response = await client_mocked.get("/api/saved/destinations")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_saved_destinations_excludes_sources(
        self, client_mocked: AsyncClient
    ):
        """List destinations does not include sources."""
        await create_saved_source(client_mocked, name="my-source")
        await create_saved_destination(client_mocked, name="my-destination")

        response = await client_mocked.get("/api/saved/destinations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "my-destination"


class TestGetSavedDestination:
    """Tests for GET /api/saved/destinations/{id}."""

    async def test_get_saved_destination_success(self, client_mocked: AsyncClient):
        """Get existing saved destination by ID."""
        dest = await create_saved_destination(client_mocked, name="test-dest")

        response = await client_mocked.get(f"/api/saved/destinations/{dest['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == dest["id"]


class TestUpdateSavedDestination:
    """Tests for PUT /api/saved/destinations/{id}."""

    async def test_update_saved_destination_success(self, client_mocked: AsyncClient):
        """Update saved destination."""
        dest = await create_saved_destination(client_mocked, name="old-name")

        response = await client_mocked.put(
            f"/api/saved/destinations/{dest['id']}",
            json={"name": "new-name"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "new-name"


class TestDeleteSavedDestination:
    """Tests for DELETE /api/saved/destinations/{id}."""

    async def test_delete_saved_destination_success(self, client_mocked: AsyncClient):
        """Delete existing saved destination."""
        dest = await create_saved_destination(client_mocked, name="to-delete")

        response = await client_mocked.delete(f"/api/saved/destinations/{dest['id']}")
        assert response.status_code == 204
