import importlib
import pytest
from app.api.deps import get_current_admin
from app.core.security import UserContext
from uuid import uuid4

def test_admin_module_exists():
    try:
        importlib.import_module("app.api.v1.endpoints.admin")
    except ImportError:
        pytest.fail("app.api.v1.endpoints.admin module not found")

@pytest.mark.asyncio
async def test_get_admin_logs(test_client):
    # Mock admin user override
    admin_user = UserContext(
        id=uuid4(),
        aud="authenticated",
        role="authenticated",
        email="admin@example.com"
    )
    
    # We need to override the dependency via app.dependency_overrides
    from app.main import app
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    
    response = await test_client.get("/api/v1/admin/logs")
    
    # Clean up override
    del app.dependency_overrides[get_current_admin]
    
    assert response.status_code == 200
