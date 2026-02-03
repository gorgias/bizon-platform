"""Tests for pipeline CRUD operations."""

import uuid

from httpx import AsyncClient

from tests.fixtures.configs import (
    MALICIOUS_TRANSFORM_IMPORT_OS,
    VALID_DUMMY_CONFIG,
    VALID_WITH_TRANSFORMS,
    YAML_INJECTION_PYTHON_OBJECT,
)


class TestCreatePipeline:
    """Tests for POST /api/pipelines."""

    async def test_create_pipeline_success(self, client_mocked: AsyncClient):
        """Create a valid pipeline."""
        response = await client_mocked.post(
            "/api/pipelines",
            json={"name": "test-pipeline", "config": VALID_DUMMY_CONFIG},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-pipeline"
        assert data["config"] == VALID_DUMMY_CONFIG
        assert data["enabled"] is True
        assert data["schedule"] is None
        assert "id" in data
        assert "created_at" in data

    async def test_create_pipeline_with_schedule(self, client_mocked: AsyncClient):
        """Create pipeline with cron schedule."""
        response = await client_mocked.post(
            "/api/pipelines",
            json={
                "name": "scheduled-pipeline",
                "config": VALID_DUMMY_CONFIG,
                "schedule": "0 9 * * *",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["schedule"] == "0 9 * * *"

    async def test_create_pipeline_disabled(self, client_mocked: AsyncClient):
        """Create pipeline in disabled state."""
        response = await client_mocked.post(
            "/api/pipelines",
            json={
                "name": "disabled-pipeline",
                "config": VALID_DUMMY_CONFIG,
                "enabled": False,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["enabled"] is False

    async def test_create_pipeline_with_transforms(self, client_mocked: AsyncClient):
        """Create pipeline with valid transforms."""
        response = await client_mocked.post(
            "/api/pipelines",
            json={"name": "transform-pipeline", "config": VALID_WITH_TRANSFORMS},
        )
        assert response.status_code == 201
        data = response.json()
        assert "transforms" in data["config"]

    async def test_create_pipeline_malicious_transform(self, client_mocked: AsyncClient):
        """Reject pipeline with malicious transform."""
        response = await client_mocked.post(
            "/api/pipelines",
            json={"name": "evil-pipeline", "config": MALICIOUS_TRANSFORM_IMPORT_OS},
        )
        assert response.status_code == 400
        assert "Security validation failed" in response.json()["detail"]

    async def test_create_pipeline_yaml_injection(self, client_mocked: AsyncClient):
        """Reject pipeline with YAML injection."""
        response = await client_mocked.post(
            "/api/pipelines",
            json={"name": "yaml-injection", "config": YAML_INJECTION_PYTHON_OBJECT},
        )
        assert response.status_code == 400
        assert "Security validation failed" in response.json()["detail"]

    async def test_create_pipeline_duplicate_name(self, client_mocked: AsyncClient):
        """Reject duplicate pipeline name."""
        await client_mocked.post(
            "/api/pipelines",
            json={"name": "duplicate-name", "config": VALID_DUMMY_CONFIG},
        )
        response = await client_mocked.post(
            "/api/pipelines",
            json={"name": "duplicate-name", "config": VALID_DUMMY_CONFIG},
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]


class TestListPipelines:
    """Tests for GET /api/pipelines."""

    async def test_list_pipelines_empty(self, client_mocked: AsyncClient):
        """List returns empty when no pipelines."""
        response = await client_mocked.get("/api/pipelines")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_pipelines_multiple(self, client_mocked: AsyncClient):
        """List returns all pipelines."""
        for i in range(3):
            await client_mocked.post(
                "/api/pipelines",
                json={"name": f"pipeline-{i}", "config": VALID_DUMMY_CONFIG},
            )

        response = await client_mocked.get("/api/pipelines")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    async def test_list_pipelines_pagination_limit(self, client_mocked: AsyncClient):
        """List respects limit parameter."""
        for i in range(5):
            await client_mocked.post(
                "/api/pipelines",
                json={"name": f"pipeline-{i}", "config": VALID_DUMMY_CONFIG},
            )

        response = await client_mocked.get("/api/pipelines?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_list_pipelines_pagination_offset(self, client_mocked: AsyncClient):
        """List respects offset parameter."""
        for i in range(5):
            await client_mocked.post(
                "/api/pipelines",
                json={"name": f"pipeline-{i}", "config": VALID_DUMMY_CONFIG},
            )

        response = await client_mocked.get("/api/pipelines?offset=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_list_pipelines_filter_enabled(self, client_mocked: AsyncClient):
        """List filters by enabled status."""
        await client_mocked.post(
            "/api/pipelines",
            json={"name": "enabled", "config": VALID_DUMMY_CONFIG, "enabled": True},
        )
        await client_mocked.post(
            "/api/pipelines",
            json={"name": "disabled", "config": VALID_DUMMY_CONFIG, "enabled": False},
        )

        response = await client_mocked.get("/api/pipelines?enabled=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "enabled"


class TestGetPipeline:
    """Tests for GET /api/pipelines/{id}."""

    async def test_get_pipeline_success(self, client_mocked: AsyncClient, pipeline_mocked: dict):
        """Get existing pipeline by ID."""
        response = await client_mocked.get(f"/api/pipelines/{pipeline_mocked['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pipeline_mocked["id"]
        assert data["name"] == pipeline_mocked["name"]

    async def test_get_pipeline_not_found(self, client_mocked: AsyncClient):
        """Get non-existent pipeline returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client_mocked.get(f"/api/pipelines/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_pipeline_invalid_uuid(self, client_mocked: AsyncClient):
        """Get with invalid UUID returns 422."""
        response = await client_mocked.get("/api/pipelines/not-a-uuid")
        assert response.status_code == 422


class TestUpdatePipeline:
    """Tests for PUT /api/pipelines/{id}."""

    async def test_update_pipeline_name(self, client_mocked: AsyncClient, pipeline_mocked: dict):
        """Update pipeline name."""
        response = await client_mocked.put(
            f"/api/pipelines/{pipeline_mocked['id']}",
            json={"name": "updated-name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated-name"

    async def test_update_pipeline_schedule(self, client_mocked: AsyncClient, pipeline_mocked: dict):
        """Update pipeline schedule."""
        response = await client_mocked.put(
            f"/api/pipelines/{pipeline_mocked['id']}",
            json={"schedule": "0 12 * * *"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["schedule"] == "0 12 * * *"

    async def test_update_pipeline_enabled(self, client_mocked: AsyncClient, pipeline_mocked: dict):
        """Update pipeline enabled status."""
        response = await client_mocked.put(
            f"/api/pipelines/{pipeline_mocked['id']}",
            json={"enabled": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False

    async def test_update_pipeline_config(self, client_mocked: AsyncClient, pipeline_mocked: dict):
        """Update pipeline config."""
        new_config = {**VALID_DUMMY_CONFIG, "name": "updated-config"}
        response = await client_mocked.put(
            f"/api/pipelines/{pipeline_mocked['id']}",
            json={"config": new_config},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["config"]["name"] == "updated-config"

    async def test_update_pipeline_not_found(self, client_mocked: AsyncClient):
        """Update non-existent pipeline returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client_mocked.put(
            f"/api/pipelines/{fake_id}",
            json={"name": "new-name"},
        )
        assert response.status_code == 404

    async def test_update_pipeline_invalid_config(self, client_mocked: AsyncClient, pipeline_mocked: dict):
        """Update with malicious config is rejected."""
        response = await client_mocked.put(
            f"/api/pipelines/{pipeline_mocked['id']}",
            json={"config": MALICIOUS_TRANSFORM_IMPORT_OS},
        )
        assert response.status_code == 400


class TestDeletePipeline:
    """Tests for DELETE /api/pipelines/{id}."""

    async def test_delete_pipeline_success(self, client_mocked: AsyncClient, pipeline_mocked: dict):
        """Delete existing pipeline."""
        response = await client_mocked.delete(f"/api/pipelines/{pipeline_mocked['id']}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = await client_mocked.get(f"/api/pipelines/{pipeline_mocked['id']}")
        assert get_response.status_code == 404

    async def test_delete_pipeline_not_found(self, client_mocked: AsyncClient):
        """Delete non-existent pipeline returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client_mocked.delete(f"/api/pipelines/{fake_id}")
        assert response.status_code == 404


class TestDuplicatePipeline:
    """Tests for POST /api/pipelines/{id}/duplicate."""

    async def test_duplicate_pipeline_success(self, client_mocked: AsyncClient, pipeline_mocked: dict):
        """Duplicate existing pipeline."""
        response = await client_mocked.post(f"/api/pipelines/{pipeline_mocked['id']}/duplicate")
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == f"{pipeline_mocked['name']} (copy)"
        assert data["config"] == pipeline_mocked["config"]
        assert data["enabled"] is False  # Duplicates start disabled

    async def test_duplicate_pipeline_unique_name(self, client_mocked: AsyncClient, pipeline_mocked: dict):
        """Duplicate generates unique names."""
        # First duplicate
        await client_mocked.post(f"/api/pipelines/{pipeline_mocked['id']}/duplicate")

        # Second duplicate should have different name
        response = await client_mocked.post(f"/api/pipelines/{pipeline_mocked['id']}/duplicate")
        assert response.status_code == 201
        data = response.json()
        assert "(copy 2)" in data["name"]

    async def test_duplicate_pipeline_not_found(self, client_mocked: AsyncClient):
        """Duplicate non-existent pipeline returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client_mocked.post(f"/api/pipelines/{fake_id}/duplicate")
        assert response.status_code == 404


class TestTriggerPipelineRun:
    """Tests for POST /api/pipelines/{id}/run."""

    async def test_trigger_run_success(self, client_mocked: AsyncClient, pipeline_mocked: dict):
        """Trigger a pipeline run."""
        response = await client_mocked.post(
            f"/api/pipelines/{pipeline_mocked['id']}/run",
            json={"triggered_by": "manual"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["triggered_by"] == "manual"
        assert data["pipeline_id"] == pipeline_mocked["id"]

    async def test_trigger_run_not_found(self, client_mocked: AsyncClient):
        """Trigger run on non-existent pipeline returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client_mocked.post(
            f"/api/pipelines/{fake_id}/run",
            json={"triggered_by": "manual"},
        )
        assert response.status_code == 404


class TestPipelineRuns:
    """Tests for pipeline run endpoints."""

    async def test_list_pipeline_runs(self, client_mocked: AsyncClient, pipeline_mocked: dict):
        """List runs for a pipeline."""
        # Create a run
        await client_mocked.post(
            f"/api/pipelines/{pipeline_mocked['id']}/run",
            json={"triggered_by": "manual"},
        )

        response = await client_mocked.get(f"/api/pipelines/{pipeline_mocked['id']}/runs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    async def test_get_run_status(self, client_mocked: AsyncClient, pipeline_mocked: dict):
        """Get status of a specific run."""
        run_response = await client_mocked.post(
            f"/api/pipelines/{pipeline_mocked['id']}/run",
            json={"triggered_by": "manual"},
        )
        run_id = run_response.json()["id"]

        response = await client_mocked.get(f"/api/pipelines/runs/{run_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run_id
        assert data["status"] == "pending"
