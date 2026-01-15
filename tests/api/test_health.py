"""Tests for health check endpoint."""

from httpx import AsyncClient


class TestHealthCheck:
    """Tests for GET /api/health."""

    async def test_health_check_returns_ok(self, client: AsyncClient):
        """Health check returns healthy status."""
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
