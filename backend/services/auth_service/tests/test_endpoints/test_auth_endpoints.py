"""Integration tests for auth endpoints - Phase 3 simplified."""

import pytest


@pytest.mark.integration
@pytest.mark.skip(
    reason="Endpoint tests require full app setup - will implement in Phase 4"
)
class TestAuthEndpointsBasic:
    """Basic auth endpoint tests."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test GET /health."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test GET /."""
        response = await client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
