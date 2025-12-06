from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, UserContext
from app.core.database import get_async_session
from app.models.log import DietaryLog
from app.schemas.analysis import AnalysisUploadRequest, AnalysisUploadResponse

router = APIRouter()

@router.post("/upload", response_model=AnalysisUploadResponse)
async def upload_analysis_data(
    request: AnalysisUploadRequest,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Record a new dietary log entry after files have been uploaded to storage.
    """
    
    # Create DB Entry
    new_log = DietaryLog(
        user_id=current_user.id,
        image_path=request.image_path,
        audio_path=request.audio_path,
        status="processing"
    )
    
    db.add(new_log)
    await db.commit()
    await db.refresh(new_log)
    
    return AnalysisUploadResponse(
        log_id=str(new_log.id), # Convert UUID to str for Pydantic if needed, though Pydantic handles UUIDs usually
        status=new_log.status
    )
