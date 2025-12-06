import jwt
from uuid import UUID
from pydantic import BaseModel
from app.config import settings

class UserContext(BaseModel):
    id: UUID
    aud: str
    role: str

def verify_token(token: str) -> UserContext:
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated", # Supabase default audience
            options={"verify_aud": True} 
        )
        
        user_id = payload.get("sub")
        if not user_id:
             raise ValueError("Token is missing 'sub' claim")

        return UserContext(
            id=UUID(user_id),
            aud=payload.get("aud", ""),
            role=payload.get("role", "")
        )
    except jwt.PyJWTError as e:
        raise ValueError(f"Invalid token: {e}")
