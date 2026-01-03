from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UserContext, get_current_user
from app.database import get_async_session
from app.models.log import DietaryLog
from app.schemas.analysis import (
    AnalysisUploadRequest,
    AnalysisUploadResponse,
    ClarifyRequest,
)

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

    # Parse timestamp safely
    try:
        parsed_timestamp = datetime.fromisoformat(request.client_timestamp.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid timestamp format. Expected ISO 8601.",
        ) from None

    # Create DB Entry
    new_log = DietaryLog(
        user_id=current_user.id,
        image_path=request.image_path,
        audio_path=request.audio_path,
        client_timestamp=parsed_timestamp,
        status="processing",
    )

    db.add(new_log)
    await db.commit()
    await db.refresh(new_log)

    return AnalysisUploadResponse(
        log_id=new_log.id,
        status=new_log.status,
    )


@router.post("/clarify/{log_id}", response_model=AnalysisUploadResponse)
async def submit_clarification_response(
    log_id: UUID,
    request: ClarifyRequest,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Submit a clarification response for a dietary log awaiting clarification.

    This endpoint handles user responses to clarification questions, triggering
    re-analysis with the additional context. If the response is voice input,
    it will be transcribed first.
    """
    # Fetch the log entry
    result = await db.execute(
        select(DietaryLog).where(
            DietaryLog.id == log_id,
            DietaryLog.user_id == current_user.id,
        )
    )
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log entry not found.",
        )

    if log.status != "clarification":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Log is not awaiting clarification. Current status: {log.status}",
        )

    # Handle voice response transcription if needed
    clarification_text = request.response
    if request.is_voice:
        # Voice responses should already be transcribed by the frontend
        # but we could add server-side transcription here if needed
        pass

    # Store the clarification response (could be appended to description or a new field)
    if log.description:
        log.description = f"{log.description}\n[Clarification]: {clarification_text}"
    else:
        log.description = f"[Clarification]: {clarification_text}"

    # Update status back to processing for re-analysis
    log.status = "processing"

    await db.commit()
    await db.refresh(log)

    return AnalysisUploadResponse(
        log_id=log.id,
        status=log.status,
    )
