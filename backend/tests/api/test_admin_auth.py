import pytest
from app.api.deps import get_current_admin
from app.core.security import UserContext
from app.config import settings
from fastapi import HTTPException
from uuid import uuid4

@pytest.fixture
def mock_admin_settings():
    original = settings.ADMIN_EMAILS
    settings.ADMIN_EMAILS = "admin@example.com, super@example.com"
    yield
    settings.ADMIN_EMAILS = original

@pytest.mark.asyncio
async def test_admin_by_role():
    user = UserContext(
        id=uuid4(),
        aud="authenticated",
        role="authenticated",
        app_metadata={"role": "admin"}
    )
    result = await get_current_admin(user)
    assert result == user

@pytest.mark.asyncio
async def test_admin_by_email(mock_admin_settings):
    user = UserContext(
        id=uuid4(),
        aud="authenticated",
        role="authenticated",
        email="admin@example.com"
    )
    result = await get_current_admin(user)
    assert result == user

@pytest.mark.asyncio
async def test_not_admin(mock_admin_settings):
    user = UserContext(
        id=uuid4(),
        aud="authenticated",
        role="authenticated",
        email="user@example.com"
    )
    with pytest.raises(HTTPException) as exc:
        await get_current_admin(user)
    assert exc.value.status_code == 403
