from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import verify_token, UserContext

# Supabase Auth uses Bearer token, usually passed in Authorization header.
# We set auto_error=False to handle 401 manually or allow optional auth.
# tokenUrl is required by OAuth2PasswordBearer for Swagger UI, but since we rely on Supabase/Client handles,
# we point it to a placeholder. Users should paste their JWT manually in the 'Authorize' dialog.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="https://api.supabase.com/v1/auth/token", auto_error=False)

async def get_current_user(token: Annotated[str | None, Depends(oauth2_scheme)]) -> UserContext:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user = verify_token(token)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
