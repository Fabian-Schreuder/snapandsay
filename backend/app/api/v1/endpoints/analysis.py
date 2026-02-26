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
        transcript=request.text_input,
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

    # Process all clarification responses (batch)
    import logging

    from app.services import voice_service

    endpoint_logger = logging.getLogger(__name__)

    all_qa_parts = []
    all_response_texts = []

    # Get questions asked for Q/A pairing
    questions_asked = []
    if log.ampm_data and "questions_asked" in log.ampm_data:
        questions_asked = log.ampm_data["questions_asked"]

    for i, resp in enumerate(request.responses):
        # Transcribe voice responses if needed
        clarification_text = resp.response
        if resp.is_voice and resp.audio_path:
            try:
                language = "nl"
                if log.ampm_data and "language" in log.ampm_data:
                    language = log.ampm_data["language"]

                clarification_text = await voice_service.transcribe_audio(
                    file_path=resp.audio_path,
                    language=language,
                    token=current_user.token,
                )
                endpoint_logger.info(
                    f"Transcribed voice clarification for '{resp.item_name}': {clarification_text}"
                )
            except Exception as e:
                endpoint_logger.error(f"Voice transcription failed for '{resp.item_name}': {e}")
                clarification_text = resp.response

        all_response_texts.append(clarification_text)

        # Pair with question if available
        question = questions_asked[i] if i < len(questions_asked) else ""
        if question:
            all_qa_parts.append(f"Q: {question}\nA: {clarification_text}")
        else:
            item_label = resp.item_name or f"item {i + 1}"
            all_qa_parts.append(f"[{item_label}]: {clarification_text}")

    # The clarification responses are now only stored in ampm_data below

    # The clarification responses are now only stored in ampm_data below

    # Append to ampm_data responses
    if log.ampm_data:
        ampm_data = dict(log.ampm_data)
        if "responses" not in ampm_data:
            ampm_data["responses"] = []
        ampm_data["responses"].extend(all_response_texts)
        log.ampm_data = ampm_data

    # Update status back to processing for re-analysis
    log.status = "processing"

    await db.commit()
    await db.refresh(log)

    return AnalysisUploadResponse(
        log_id=log.id,
        status=log.status,
    )
