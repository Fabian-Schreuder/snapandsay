from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException

from app.api.deps import get_current_user
from app.config import settings
from app.core.security import UserContext, verify_token


# Override API key for testing
# Override API key for testing using a fixture to avoid side effects
@pytest.fixture(autouse=True)
def mock_settings():
    original_secret = settings.SUPABASE_JWT_SECRET
    original_aud = settings.SUPABASE_AUTH_AUDIENCE

    settings.SUPABASE_JWT_SECRET = "supersecretkey"
    settings.SUPABASE_AUTH_AUDIENCE = "authenticated"

    yield

    # Restore
    settings.SUPABASE_JWT_SECRET = original_secret
    settings.SUPABASE_AUTH_AUDIENCE = original_aud


def create_token(uid: str = None, aud: str = "authenticated", role: str = "authenticated"):
    if uid is None:
        uid = str(uuid4())
    payload = {"sub": uid, "aud": aud, "role": role}
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


def test_verify_token_valid():
    uid = str(uuid4())
    token = create_token(uid=uid)
    user = verify_token(token)
    assert str(user.id) == uid
    assert user.aud == "authenticated"


def test_verify_token_invalid_signature():
    token = create_token()
    # Tamper with token
    invalid_token = token + "scramble"
    with pytest.raises(ValueError):
        verify_token(invalid_token)


@pytest.mark.asyncio
async def test_get_current_user_valid():
    token = create_token()
    user = await get_current_user(token)
    assert isinstance(user, UserContext)


@pytest.mark.asyncio
async def test_get_current_user_no_token():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    with pytest.raises(HTTPException) as exc:
        await get_current_user("invalid")
    assert exc.value.status_code == 401


def test_verify_token_anon_role():
    """Verify that tokens with 'anon' role are accepted."""
    uid = str(uuid4())
    token = create_token(uid=uid, role="anon")
    user = verify_token(token)
    assert str(user.id) == uid
    assert user.role == "anon"
