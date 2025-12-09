import importlib
import pytest
from app.api.deps import get_current_admin
from app.core.security import UserContext
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from app.models.log import DietaryLog
from sqlalchemy import text
from app.main import app

def test_admin_module_exists():
    try:
        importlib.import_module("app.api.v1.endpoints.admin")
    except ImportError:
        pytest.fail("app.api.v1.endpoints.admin module not found")

import importlib
import pytest
from unittest.mock import AsyncMock, patch
from app.api.deps import get_current_admin
from app.core.security import UserContext
from uuid import uuid4
from datetime import datetime, date
from app.main import app

def test_admin_module_exists():
    try:
        importlib.import_module("app.api.v1.endpoints.admin")
    except ImportError:
        pytest.fail("app.api.v1.endpoints.admin module not found")

@pytest.fixture
def override_admin_auth():
    admin_user = UserContext(
        id=uuid4(),
        aud="authenticated",
        role="authenticated",
        email="admin@example.com",
        app_metadata={"role": "admin"}
    )
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    yield
    if get_current_admin in app.dependency_overrides:
        del app.dependency_overrides[get_current_admin]

@pytest.mark.asyncio
async def test_get_admin_logs_filtering(test_client, override_admin_auth):
    user_id = uuid4()
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 31)
    
    mock_logs = [
        {
            "id": uuid4(),
            "user_id": user_id,
            "status": "logged",
            "created_at": datetime.now(),
            "image_path": "path/to/image",
            "description": "Test log",
            "needs_review": False
        }
    ]
    
    with patch("app.api.v1.endpoints.admin.log_service") as mock_service:
        mock_service.get_all_logs = AsyncMock(return_value=mock_logs)
        mock_service.count_all_logs = AsyncMock(return_value=1)
        
        # Test 1: Full Filters
        response = await test_client.get(
            f"/api/v1/admin/logs?user_id={user_id}&start_date={start_date}&end_date={end_date}&page=1&size=10"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["meta"]["total"] == 1
        
        # Verify service calls with kwargs
        call_kwargs = mock_service.get_all_logs.call_args.kwargs
        assert str(call_kwargs["user_id"]) == str(user_id)
        assert call_kwargs["start_date"] == start_date
        assert call_kwargs["end_date"] == end_date
        assert call_kwargs["page"] == 1
        
        # Test 2: Pagination Defaults
        mock_service.get_all_logs.reset_mock()
        response = await test_client.get("/api/v1/admin/logs")
        assert response.status_code == 200
        
        call_kwargs = mock_service.get_all_logs.call_args.kwargs
        assert call_kwargs["limit"] == 50 # Default from endpoint definition
        assert call_kwargs["page"] == 1
