from typing import Optional
from datetime import date, datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from app.api.deps import get_current_admin, get_db
from app.core.security import UserContext
from app.schemas.log import DietaryLogListResponse, LogListMeta
from app.services import log_service, export_service
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
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    min_calories: Optional[int] = Query(None, description="Minimum calories"),
    max_calories: Optional[int] = Query(None, description="Maximum calories")
):
    """
    Get all logs with filtering for admin dashboard.
    """
    logs = await log_service.get_all_logs(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        min_calories=min_calories,
        max_calories=max_calories,
        page=page,
        limit=limit
    )
    
    total = await log_service.count_all_logs(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        min_calories=min_calories,
        max_calories=max_calories
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

@router.get("/export")
async def get_export_logs(
    format: str = Query("csv", description="Export format: csv or json"),
    user_id: Optional[UUID] = Query(None, description="Filter by User ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    min_calories: Optional[int] = Query(None, description="Minimum calories"),
    max_calories: Optional[int] = Query(None, description="Maximum calories"),
    current_user: UserContext = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Export dietary logs in CSV or JSON format.
    """
    if format not in ["csv", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Supported formats: csv, json"
        )

    # Fetch logs with filters (using high limit for export)
    limit = 10000
    
    logs = await log_service.get_all_logs(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        min_calories=min_calories,
        max_calories=max_calories,
        page=1,
        limit=limit,
        with_user=True
    )
    
    filename_ts = datetime.now().strftime("%Y%m%d_%H%M")
    
    if format == "csv":
        generator = export_service.export_logs_as_csv(logs)
        content_type = "text/csv; charset=utf-8"
        filename = f"snapandsay_export_{filename_ts}.csv"
    else:
        generator = export_service.export_logs_as_json(logs)
        content_type = "application/json"
        filename = f"snapandsay_export_{filename_ts}.json"
        
    return StreamingResponse(
        generator,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
