"""Service layer for dietary log operations."""
from datetime import datetime, time, timezone, date
from typing import List, Optional
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


async def get_log_by_id(
    db: AsyncSession, user_id: UUID, log_id: UUID
) -> Optional[DietaryLog]:
    """
    Retrieve a single dietary log by ID.
    
    Args:
        db: Database session
        user_id: User ID to verify ownership
        log_id: Log ID to retrieve
    
    Returns:
        DietaryLog if found and owned by user, None otherwise
    """
    result = await db.execute(
        select(DietaryLog).where(
            DietaryLog.id == log_id,
            DietaryLog.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def update_log(
    db: AsyncSession, user_id: UUID, log_id: UUID, update_data: dict
) -> Optional[DietaryLog]:
    """
    Update a dietary log entry.
    
    Args:
        db: Database session
        user_id: User ID to verify ownership
        log_id: Log ID to update
        update_data: Dictionary of fields to update
    
    Returns:
        Updated DietaryLog if found and owned by user, None otherwise
    """
    result = await db.execute(
        select(DietaryLog).where(
            DietaryLog.id == log_id,
            DietaryLog.user_id == user_id
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        return None
    
    for key, value in update_data.items():
        setattr(log, key, value)
    
    await db.commit()
    await db.refresh(log)
    return log


async def delete_log(
    db: AsyncSession, user_id: UUID, log_id: UUID
) -> bool:
    """
    Delete a dietary log entry.
    
    Args:
        db: Database session
        user_id: User ID to verify ownership
        log_id: Log ID to delete
    
    Returns:
        True if deleted, False if not found or not owned
    """
    result = await db.execute(
        select(DietaryLog).where(
            DietaryLog.id == log_id,
            DietaryLog.user_id == user_id
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        return False
    
    await db.delete(log)
    await db.commit()
    return True
