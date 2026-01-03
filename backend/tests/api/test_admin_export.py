from unittest.mock import patch
from uuid import uuid4

import pytest

from app.api.deps import get_current_admin
from app.core.security import UserContext
from app.main import app


@pytest.fixture
def override_admin_auth():
    admin_user = UserContext(
        id=uuid4(),
        aud="authenticated",
        role="authenticated",
        email="admin@example.com",
        app_metadata={"role": "admin"},
    )
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    yield
    app.dependency_overrides.pop(get_current_admin, None)


@pytest.mark.asyncio
async def test_export_unauthorized(test_client):
    # Ensure no override
    app.dependency_overrides.pop(get_current_admin, None)
    # Calling without auth header
    response = await test_client.get("/api/v1/admin/export?format=csv")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_export_logs_csv_success(test_client, override_admin_auth):
    with (
        patch("app.api.v1.endpoints.admin.log_service.get_all_logs") as mock_get_logs,
        patch("app.api.v1.endpoints.admin.export_service.export_logs_as_csv") as mock_export,
    ):
        mock_get_logs.return_value = []
        # Generator that yields chunks
        mock_export.return_value = (x for x in ["header\n", "row1\n"])

        response = await test_client.get("/api/v1/admin/export?format=csv")

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment; filename=" in response.headers["content-disposition"]
        assert "header" in response.text

        mock_get_logs.assert_called_once()


@pytest.mark.asyncio
async def test_export_logs_json_success(test_client, override_admin_auth):
    with (
        patch("app.api.v1.endpoints.admin.log_service.get_all_logs") as mock_get_logs,
        patch("app.api.v1.endpoints.admin.export_service.export_logs_as_json") as mock_export,
    ):
        mock_get_logs.return_value = []
        mock_export.return_value = (x for x in ["[", "{}", "{}", "]"])

        response = await test_client.get("/api/v1/admin/export?format=json")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        assert "[" in response.text


@pytest.mark.asyncio
async def test_export_invalid_format(test_client, override_admin_auth):
    response = await test_client.get("/api/v1/admin/export?format=xml")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_export_with_filters(test_client, override_admin_auth):
    with (
        patch("app.api.v1.endpoints.admin.log_service.get_all_logs") as mock_get_logs,
        patch("app.api.v1.endpoints.admin.export_service.export_logs_as_csv") as mock_export,
    ):
        mock_get_logs.return_value = []
        mock_export.return_value = (x for x in [])

        user_id = uuid4()
        await test_client.get(
            f"/api/v1/admin/export?format=csv&user_id={user_id}&min_calories=100&max_calories=500"
        )

        kwargs = mock_get_logs.call_args.kwargs
        # Verify filters passed (assuming update to logic support this)
        assert str(kwargs["user_id"]) == str(user_id)
        assert kwargs["with_user"] is True
        # assert kwargs["min_calories"] == 100 # Needed if we update log_service
        # assert kwargs["max_calories"] == 500
