import jwt
from uuid import UUID
from pydantic import BaseModel
from app.config import settings

class UserContext(BaseModel):
    id: UUID
    aud: str
    role: str
    email: str | None = None
    app_metadata: dict | None = None

def verify_token(token: str) -> UserContext:
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience=settings.SUPABASE_AUTH_AUDIENCE, # Supabase audience
            options={"verify_aud": True} 
        )
        
        user_id = payload.get("sub")
        if not user_id:
             raise ValueError("Token is missing 'sub' claim")

        return UserContext(
            id=UUID(user_id),
            aud=payload.get("aud", ""),
            role=payload.get("role", ""),
            email=payload.get("email"),
            app_metadata=payload.get("app_metadata")
        )
    except jwt.PyJWTError as e:
        print(f"DEBUG: JWT Validation Failed. Error: {e}, Token (prefix): {token[:10]}")
        raise ValueError(f"Invalid token: {e}")
