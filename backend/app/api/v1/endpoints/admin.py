from typing import Optional
from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status
from app.api.deps import get_current_admin, get_db
from app.core.security import UserContext
from app.schemas.log import DietaryLogListResponse, LogListMeta
from app.services import log_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/logs", response_model=DietaryLogListResponse)
async def get_admin_logs(
    current_user: UserContext = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[UUID] = Query(None, description="Filter by User ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page")
):
    """
    Get all logs with filtering for admin dashboard.
    """
    logs = await log_service.get_all_logs(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit
    )
    
    total = await log_service.count_all_logs(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )

    return DietaryLogListResponse(
        data=logs,
        meta=LogListMeta(
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit
        )
    )
