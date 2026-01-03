from uuid import UUID

import jwt
from pydantic import BaseModel

from app.config import settings


class UserContext(BaseModel):
    id: UUID
    aud: str
    role: str
    email: str | None = None
    app_metadata: dict | None = None


# Cache for PyJWKClient to avoid fetching keys on every request
_jwks_client = None


def get_jwks_client():
    global _jwks_client
    if _jwks_client is None:
        if not settings.SUPABASE_URL:
            raise ValueError("SUPABASE_URL is not set in settings, but is required for JWKS verification.")
        jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        # PyJWKClient handles caching of keys internally
        _jwks_client = jwt.PyJWKClient(jwks_url)
    return _jwks_client


def verify_token(token: str) -> UserContext:
    try:
        # 1. Decode header to determine algorithm
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg")

        if alg == "HS256":
            # Symmetric key validation
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience=settings.SUPABASE_AUTH_AUDIENCE,
                options={"verify_aud": True},
            )
        elif alg in ["RS256", "ES256"]:
            # Asymmetric key validation via JWKS
            signing_key = get_jwks_client().get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=[alg],
                audience=settings.SUPABASE_AUTH_AUDIENCE,
                options={"verify_aud": True},
            )
        else:
            raise ValueError(f"Unsupported algorithm: {alg}")

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Token is missing 'sub' claim")

        return UserContext(
            id=UUID(user_id),
            aud=payload.get("aud", ""),
            role=payload.get("role", ""),
            email=payload.get("email"),
            app_metadata=payload.get("app_metadata"),
        )
    except jwt.PyJWTError as e:
        print(
            f"DEBUG: JWT Validation Failed. Error: {e}, " f"Token Header: {jwt.get_unverified_header(token)}"
        )
        raise ValueError(f"Invalid token: {e}") from e
