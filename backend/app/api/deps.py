import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import UserContext, verify_token
from app.database import get_async_session as get_db
from app.models.user import User

# Supabase Auth uses Bearer token, usually passed in Authorization header.
# We set auto_error=False to handle 401 manually or allow optional auth.
# tokenUrl is required by OAuth2PasswordBearer for Swagger UI, but since we rely on Supabase/Client handles,
# we point it to a placeholder. Users should paste their JWT manually in the 'Authorize' dialog.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="https://api.supabase.com/v1/auth/token", auto_error=False)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)
) -> UserContext:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_ctx = verify_token(token)

        # Ensure user exists in local database (sync with Supabase Auth)
        # This prevents ForeignKeyViolationError in log tables
        result = await db.execute(select(User).where(User.id == user_ctx.id))
        db_user = result.scalar_one_or_none()

        if not db_user:
            # Create user profile if missing
            new_user = User(
                id=user_ctx.id,
                # Generate a random anonymous ID if one doesn't exist
                anonymous_id=f"user_{secrets.token_hex(4)}",
            )
            db.add(new_user)
            try:
                await db.commit()
            except IntegrityError:
                # Handle race condition where user might have been created concurrently
                await db.rollback()

        return user_ctx
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


async def get_current_admin(user: Annotated[UserContext, Depends(get_current_user)]) -> UserContext:
    # Check if user has admin role in app_metadata
    if user.app_metadata and user.app_metadata.get("role") == "admin":
        return user

    # Check if user email is in ADMIN_EMAILS
    if user.email and settings.ADMIN_EMAILS:
        admin_emails = [e.strip() for e in settings.ADMIN_EMAILS.split(",")]
        if user.email in admin_emails:
            return user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized",
    )
