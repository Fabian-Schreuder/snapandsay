"""Service layer for dietary log operations."""
from datetime import UTC, date, datetime, time
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.log import DietaryLog


async def get_all_logs(
    db: AsyncSession,
    page: int = 1,
    limit: int = 50,
    user_id: UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    min_calories: int | None = None,
    max_calories: int | None = None,
    with_user: bool = False
) -> list[DietaryLog]:
    """
    Retrieve all logs with filtering and pagination for admin.
    """
    query = select(DietaryLog).order_by(DietaryLog.created_at.desc())
    
    if with_user:
        query = query.options(joinedload(DietaryLog.user))
    
    if user_id:
        query = query.where(DietaryLog.user_id == user_id)
        
    if start_date:
        start_dt = datetime.combine(start_date, time.min, tzinfo=UTC)
        query = query.where(DietaryLog.created_at >= start_dt)
        
    if end_date:
        end_dt = datetime.combine(end_date, time.max, tzinfo=UTC)
        query = query.where(DietaryLog.created_at <= end_dt)

    if min_calories is not None:
        query = query.where(DietaryLog.calories >= min_calories)

    if max_calories is not None:
        query = query.where(DietaryLog.calories <= max_calories)
        
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    return list(result.unique().scalars().all())


async def count_all_logs(
    db: AsyncSession,
    user_id: UUID | None = None,
    dataset = None, # unused but kept for signature compatibility if needed? No, just addargs
    start_date: date | None = None,
    end_date: date | None = None,
    min_calories: int | None = None,
    max_calories: int | None = None
) -> int:
    """
    Count total logs matching filters.
    """
    query = select(func.count()).select_from(DietaryLog)
    
    if user_id:
        query = query.where(DietaryLog.user_id == user_id)
        
    if start_date:
        start_dt = datetime.combine(start_date, time.min, tzinfo=UTC)
        query = query.where(DietaryLog.created_at >= start_dt)
        
    if end_date:
        end_dt = datetime.combine(end_date, time.max, tzinfo=UTC)
        query = query.where(DietaryLog.created_at <= end_dt)
        
    if min_calories is not None:
        query = query.where(DietaryLog.calories >= min_calories)

    if max_calories is not None:
        query = query.where(DietaryLog.calories <= max_calories)
        
    result = await db.execute(query)
    return result.scalar() or 0



async def get_logs_for_date(
    db: AsyncSession, user_id: UUID, target_date: date
) -> list[DietaryLog]:
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
    start = datetime.combine(target_date, time.min, tzinfo=UTC)
    end = datetime.combine(target_date, time.max, tzinfo=UTC)
    
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
) -> DietaryLog | None:
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
) -> DietaryLog | None:
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
