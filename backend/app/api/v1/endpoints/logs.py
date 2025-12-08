"""API endpoints for dietary log operations."""
from datetime import datetime, timezone, date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, UserContext
from app.database import get_async_session
from app.schemas.log import DietaryLogListResponse, DietaryLogResponse, LogListMeta
from app.services.log_service import get_logs_for_date

router = APIRouter()


@router.get("", response_model=DietaryLogListResponse)
async def get_logs(
    date: Optional[str] = None,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> DietaryLogListResponse:
    """
    Get dietary logs for a specific date.
    
    Args:
        date: ISO format date string (YYYY-MM-DD). Defaults to today in UTC.
        current_user: Authenticated user context
        db: Database session
    
    Returns:
        List of dietary logs for the specified date
    """
    # Parse date or default to today
    if date:
        try:
            target_date = datetime.fromisoformat(date).date()
        except ValueError:
            # Fall back to today if invalid format
            target_date = datetime.now(timezone.utc).date()
    else:
        target_date = datetime.now(timezone.utc).date()
    
    # Fetch logs from service layer
    logs = await get_logs_for_date(db, current_user.id, target_date)
    
    # Convert to response schema
    log_responses = [
        DietaryLogResponse.model_validate(log) for log in logs
    ]
    
    return DietaryLogListResponse(
        data=log_responses,
        meta=LogListMeta(total=len(log_responses))
    )
