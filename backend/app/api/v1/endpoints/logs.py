"""API endpoints for dietary log operations."""
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UserContext, get_current_user
from app.database import get_async_session
from app.schemas.log import (
    DietaryLogListResponse,
    DietaryLogResponse,
    DietaryLogUpdateRequest,
    LogListMeta,
)
from app.services import log_service

router = APIRouter()


@router.get("", response_model=DietaryLogListResponse)
async def get_logs(
    date: str | None = None,
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
            target_date = datetime.now(UTC).date()
    else:
        target_date = datetime.now(UTC).date()
    
    # Fetch logs from service layer
    logs = await log_service.get_logs_for_date(db, current_user.id, target_date)
    
    # Generate signed URLs
    from app.core.supabase import get_supabase_client
    supabase = get_supabase_client()
    
    log_responses = []
    for log in logs:
        response_model = DietaryLogResponse.model_validate(log)
        try:
            # Generate signed URL valid for 1 hour (3600 seconds)
            signed_url = supabase.storage.from_("raw_uploads").create_signed_url(
                log.image_path, 3600
            )
            response_model.image_url = signed_url["signedURL"]
        except Exception as e:
            # Fallback to path if signing fails
            print(f"Failed to sign URL for {log.image_path}: {e}")
            pass
        log_responses.append(response_model)
    
    return DietaryLogListResponse(
        data=log_responses,
        meta=LogListMeta(total=len(log_responses))
    )


@router.get("/{log_id}", response_model=DietaryLogResponse)
async def get_log(
    log_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> DietaryLogResponse:
    """
    Get a single dietary log by ID.
    
    Args:
        log_id: UUID of the log to retrieve
        current_user: Authenticated user context
        db: Database session
    
    Returns:
        Dietary log entry
    
    Raises:
        HTTPException: 404 if log not found or not owned by user
    """
    log = await log_service.get_log_by_id(db, current_user.id, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
        
    response_model = DietaryLogResponse.model_validate(log)
    try:
        from app.core.supabase import get_supabase_client
        supabase = get_supabase_client()
        signed_url = supabase.storage.from_("raw_uploads").create_signed_url(
            log.image_path, 3600
        )
        response_model.image_url = signed_url["signedURL"]
    except Exception as e:
        print(f"Failed to sign URL for {log.image_path}: {e}")
        pass
        
    return response_model


@router.put("/{log_id}", response_model=DietaryLogResponse)
async def update_log(
    log_id: UUID,
    update_data: DietaryLogUpdateRequest,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> DietaryLogResponse:
    """
    Update a dietary log entry.
    
    Args:
        log_id: UUID of the log to update
        update_data: Fields to update (partial update supported)
        current_user: Authenticated user context
        db: Database session
    
    Returns:
        Updated dietary log entry
    
    Raises:
        HTTPException: 404 if log not found or not owned by user
    """
    updated = await log_service.update_log(
        db, current_user.id, log_id, update_data.model_dump(exclude_unset=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Log not found")
        
    response_model = DietaryLogResponse.model_validate(updated)
    try:
        from app.core.supabase import get_supabase_client
        supabase = get_supabase_client()
        signed_url = supabase.storage.from_("raw_uploads").create_signed_url(
            updated.image_path, 3600
        )
        response_model.image_url = signed_url["signedURL"]
    except Exception:
        pass
        
    return response_model


@router.delete("/{log_id}", status_code=204)
async def delete_log(
    log_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """
    Delete a dietary log entry.
    
    Args:
        log_id: UUID of the log to delete
        current_user: Authenticated user context
        db: Database session
    
    Raises:
        HTTPException: 404 if log not found or not owned by user
    """
    deleted = await log_service.delete_log(db, current_user.id, log_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Log not found")
