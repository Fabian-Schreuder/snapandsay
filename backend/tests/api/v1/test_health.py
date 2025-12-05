import pytest
from httpx import AsyncClient

from app.config import settings


@pytest.mark.asyncio
async def test_health_check(test_client: AsyncClient):
    resp = await test_client.get(f"{settings.API_V1_STR}/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_root_health_check(test_client: AsyncClient):
    """Test root-level health endpoint for load balancers."""
    resp = await test_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
