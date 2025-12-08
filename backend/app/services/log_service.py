"""Service layer for dietary log operations."""
from datetime import datetime, time, timezone, date
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import DietaryLog


async def get_logs_for_date(
    db: AsyncSession, user_id: UUID, target_date: date
) -> List[DietaryLog]:
    """
    Retrieve dietary logs for a specific date.
    
    Args:
        db: Database session
        user_id: User ID to filter logs
        target_date: Date to filter logs (UTC)
    
    Returns:
        List of DietaryLog entries for the specified date, 
        filtered to status='logged', ordered by created_at DESC
    """
    # Calculate UTC day boundaries
    start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
    end = datetime.combine(target_date, time.max, tzinfo=timezone.utc)
    
    result = await db.execute(
        select(DietaryLog)
        .where(
            DietaryLog.user_id == user_id,
            DietaryLog.status == "logged",
            DietaryLog.created_at >= start,
            DietaryLog.created_at <= end,
        )
        .order_by(DietaryLog.created_at.desc())
    )
    
    return list(result.scalars().all())
