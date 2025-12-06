import pytest
import jwt
from uuid import uuid4
from fastapi import HTTPException
from app.core.security import verify_token, UserContext
from app.api.deps import get_current_user
from app.config import settings

# Override API key for testing
settings.SUPABASE_JWT_SECRET = "supersecretkey"

def create_token(uid: str = None, aud: str = "authenticated", role: str = "authenticated"):
    if uid is None:
        uid = str(uuid4())
    payload = {
        "sub": uid,
        "aud": aud,
        "role": role
    }
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
