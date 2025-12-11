from typing import AsyncGenerator
from datetime import datetime, timezone
from uuid import UUID

from app.agent.state import AgentState
from app.services import voice_service, llm_service
from app.agent.constants import (
    STEP_ANALYZING,
    STEP_CLARIFYING,
    STEP_FINALIZING,
    MSG_ANALYZING_START,
    MSG_ANALYZING_TOKENS,
    MSG_ANALYZING_COMPLETE,
    MSG_CLARIFYING,
    MSG_FINALIZING,
    EVENT_THOUGHT,
    EVENT_RESPONSE,
    EVENT_ERROR,
    EVENT_CLARIFICATION,
    CONFIDENCE_THRESHOLD,
)
from app.schemas.sse import SSEEvent, AgentThought, AgentResponse, AgentError, AgentClarification
from app.schemas.analysis import FoodItem

from app.database import async_session_maker
from app.models.log import DietaryLog
from sqlalchemy import select

import logging

logger = logging.getLogger(__name__)


async def analyze_input(state: AgentState) -> dict:
    """
    Analyze the input (image or text) to determine the next step.
    fetches clarification context from DB if log_id exists.
    """
    image_url = state.get("image_url")
    audio_url = state.get("audio_url")
    user_token = state.get("user_token")
    transcript = None
    context = None
    
    # Fetch context from DB if this is a re-run
    if log_id:
        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(DietaryLog).where(DietaryLog.id == log_id)
                )
                log_entry = result.scalar_one_or_none()
                if log_entry and log_entry.description:
                    context = log_entry.description
                    logger.info(f"Using context from log {log_id}: {context[:50]}...")
        except Exception as e:
            logger.warning(f"Failed to fetch log context: {e}")

    if audio_url:
        logger.info(f"Transcribing audio from {audio_url}")
        try:
            transcript = await voice_service.transcribe_audio(audio_url, token=user_token)
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            if image_url:
                logger.warning("Audio transcription failed, but image provided. Proceeding with image only.")
                transcript = None
            else:
                raise e
            
    if not image_url and not transcript:
        logger.warning("No input provided for analysis")
        return {}
        
    logger.info("Analyzing multimodal input")
    try:
        result = await llm_service.analyze_multimodal(
            image_url=image_url, 
            transcript=transcript,
            context=context,
            user_token=user_token
        )
        return {
            "nutritional_data": result.model_dump(),
            "overall_confidence": result.overall_confidence,
        }
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise e


async def analyze_input_streaming(
    state: AgentState,
) -> AsyncGenerator[SSEEvent | dict, None]:
    """
    Analyze input with streaming SSE events.

    Yields SSEEvent objects during processing, and finally yields
    the state update dict with nutritional_data and overall_confidence.
    """
    image_url = state.get("image_url")
    audio_url = state.get("audio_url")
    log_id = state.get("log_id")
    user_token = state.get("user_token")
    transcript = None
    context = None
    
    # Fetch context from DB if this is a re-run
    if log_id:
        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(DietaryLog).where(DietaryLog.id == log_id)
                )
                log_entry = result.scalar_one_or_none()
                if log_entry and log_entry.description:
                    context = log_entry.description
                    logger.info(f"Using context from log {log_id}: {context[:50]}...")
        except Exception as e:
            logger.warning(f"Failed to fetch log context: {e}")

    # Emit start thought
    yield SSEEvent(
        type=EVENT_THOUGHT,
        payload=AgentThought(
            step=STEP_ANALYZING,
            message=MSG_ANALYZING_START,
            timestamp=datetime.now(timezone.utc),
        ),
    )

    if audio_url:
        logger.info(f"Transcribing audio from {audio_url}")
        try:
            transcript = await voice_service.transcribe_audio(audio_url, token=user_token)
            
            # Persist transcript
            if log_id:
                try:
                    async with async_session_maker() as session:
                        result = await session.execute(
                            select(DietaryLog).where(DietaryLog.id == log_id)
                        )
                        log_entry = result.scalar_one_or_none()
                        if log_entry:
                            log_entry.transcript = transcript
                            await session.commit()
                            logger.info(f"Persisted transcript for log {log_id}")
                except Exception as db_err:
                    logger.error(f"Failed to persist transcript: {db_err}")
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            if image_url:
                logger.warning("Audio transcription failed, but image provided. Proceeding with image only.")
                transcript = None
            else:
                yield SSEEvent(
                    type=EVENT_ERROR,
                    payload=AgentError(
                        code="TRANSCRIPTION_ERROR",
                        message="I'm having trouble understanding the audio.",
                    ),
                )
                return

    if not image_url and not transcript:
        logger.warning("No input provided for analysis")
        yield SSEEvent(
            type=EVENT_ERROR,
            payload=AgentError(
                code="NO_INPUT_ERROR",
                message="I didn't receive any image or voice input to analyze.",
            ),
        )
        return

    logger.info("Analyzing multimodal input with streaming")

    # Token callback to emit thought events during LLM generation
    token_count = 0
    
    async def on_token(token: str):
        nonlocal token_count
        token_count += 1
        # Emit a thought event every 20 tokens to show liveness without flooding
        # yield removed to strictly TypeCheck: on_token must be Awaitable[None] (coroutine), not AsyncGenerator.
        # Use a Queue or other mechanism if streaming feedback is strictly required while blocked.
        if token_count % 20 == 0:
            logger.debug(f"Streaming token count: {token_count}")

    try:
        result = await llm_service.analyze_multimodal_streaming(
            image_url=image_url, 
            transcript=transcript,
            context=context,
            on_token=on_token,
            user_token=user_token
        )
        
        # Emit complete thought
        yield SSEEvent(
            type=EVENT_THOUGHT,
            payload=AgentThought(
                step=STEP_ANALYZING,
                message=MSG_ANALYZING_COMPLETE,
                timestamp=datetime.now(timezone.utc),
            ),
        )

        yield {
            "nutritional_data": result.model_dump(),
            "overall_confidence": result.overall_confidence,
        }
    except Exception as e:
        logger.error(f"Analysis streaming failed: {e}")
        
        # Update log status to failed
        if log_id:
            try:
                async with async_session_maker() as session:
                    result = await session.execute(
                        select(DietaryLog).where(DietaryLog.id == log_id)
                    )
                    log_entry = result.scalar_one_or_none()
                    if log_entry:
                        log_entry.status = "failed"
                        # Append error to description for debugging
                        current_desc = log_entry.description or ""
                        log_entry.description = f"{current_desc}\n[Analysis Failed]: {str(e)}".strip()
                        await session.commit()
                        logger.info(f"Updated log {log_id} status to 'failed'")
            except Exception as db_err:
                logger.error(f"Failed to update log status to failed: {db_err}")

        yield SSEEvent(
            type=EVENT_ERROR,
            payload=AgentError(
                code="ANALYSIS_ERROR",
                message="I encountered an error while analyzing your meal.",
            ),
        )


async def generate_clarification(state: AgentState) -> dict:
    """
    Generate a clarification question for low-confidence items.
    """
    nutritional_data = state.get("nutritional_data", {})
    items = nutritional_data.get("items", [])
    clarification_count = state.get("clarification_count", 0)
    
    # Find low-confidence items
    low_confidence_items = [
        FoodItem(**item) for item in items 
        if item.get("confidence", 1.0) < CONFIDENCE_THRESHOLD
    ]
    
    if low_confidence_items:
        question = await llm_service.generate_clarification_question(low_confidence_items)
        return {
            "needs_clarification": True,
            "clarification_count": clarification_count + 1,
        }
    
    return {"needs_clarification": False}


async def generate_clarification_streaming(
    state: AgentState,
) -> AsyncGenerator[SSEEvent | dict, None]:
    """Generate clarification with streaming events."""
    yield SSEEvent(
        type=EVENT_THOUGHT,
        payload=AgentThought(
            step=STEP_CLARIFYING,
            message=MSG_CLARIFYING,
            timestamp=datetime.now(timezone.utc),
        ),
    )
    
    nutritional_data = state.get("nutritional_data", {})
    items = nutritional_data.get("items", [])
    clarification_count = state.get("clarification_count", 0)
    log_id = state.get("log_id")
    
    # Find low-confidence items
    low_confidence_items = [
        FoodItem(**item) for item in items 
        if item.get("confidence", 1.0) < CONFIDENCE_THRESHOLD
    ]
    
    if low_confidence_items and log_id:
        try:
            question = await llm_service.generate_clarification_question(low_confidence_items)
            
            # Update log status to clarification in database
            async with async_session_maker() as session:
                result = await session.execute(
                    select(DietaryLog).where(DietaryLog.id == log_id)
                )
                log_entry = result.scalar_one_or_none()
                if log_entry:
                    log_entry.status = "clarification"
                    await session.commit()
                    logger.info(f"Updated log {log_id} status to 'clarification'")
            
            # Build context with low-confidence items for the clarification payload
            context = {
                "items": [
                    {"name": item.name, "confidence": item.confidence}
                    for item in low_confidence_items
                ]
            }
            
            # Emit clarification event
            yield SSEEvent(
                type=EVENT_CLARIFICATION,
                payload=AgentClarification(
                    question=question.question,
                    options=question.options,
                    context=context,
                    log_id=log_id,
                ),
            )
            
            yield {
                "needs_clarification": True,
                "clarification_count": clarification_count + 1,
            }
        except Exception as e:
            logger.error(f"Clarification generation failed: {e}")
            yield {"needs_clarification": False}
    else:
        yield {"needs_clarification": False}


async def finalize_log(state: AgentState) -> dict:
    """
    Finalize the log entry after sufficient information has been gathered.
    Updates the DietaryLog record with nutritional data and final status.
    """
    needs_review = state.get("needs_review", False)
    clarification_count = state.get("clarification_count", 0)
    overall_confidence = state.get("overall_confidence", 0.0)
    
    # Mark for review if confidence is still low after max attempts
    if overall_confidence < CONFIDENCE_THRESHOLD and clarification_count >= 2:
        needs_review = True
    
    return {
        "needs_review": needs_review,
    }


async def finalize_log_streaming(
    state: AgentState,
) -> AsyncGenerator[SSEEvent | dict, None]:
    """Finalize log with streaming events and DB persistence."""
    yield SSEEvent(
        type=EVENT_THOUGHT,
        payload=AgentThought(
            step=STEP_FINALIZING,
            message=MSG_FINALIZING,
            timestamp=datetime.now(timezone.utc),
        ),
    )
    
    log_id = state.get("log_id")
    nutritional_data = state.get("nutritional_data", {})
    needs_review = state.get("needs_review", False)
    clarification_count = state.get("clarification_count", 0)
    overall_confidence = state.get("overall_confidence", 0.0)
    
    # Mark for review if confidence is still low after max attempts
    if overall_confidence < CONFIDENCE_THRESHOLD and clarification_count >= 2:
        needs_review = True
    
    # Persist to database
    if log_id:
        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(DietaryLog).where(DietaryLog.id == log_id)
                )
                log_entry = result.scalar_one_or_none()
                
                if log_entry:
                    # Update status
                    log_entry.status = "logged"
                    log_entry.needs_review = needs_review
                    
                    # Persist nutritional data
                    items = nutritional_data.get("items", [])
                    if items:
                        # Calculate totals from items
                        total_calories = sum(item.get("calories", 0) or 0 for item in items)
                        total_protein = sum(item.get("protein", 0) or 0 for item in items)
                        total_carbs = sum(item.get("carbs", 0) or 0 for item in items)
                        total_fats = sum(item.get("fats", 0) or 0 for item in items)
                        
                        log_entry.calories = total_calories if total_calories > 0 else None
                        log_entry.protein = total_protein if total_protein > 0 else None
                        log_entry.carbs = total_carbs if total_carbs > 0 else None
                        log_entry.fats = total_fats if total_fats > 0 else None
                        
                        # Extract meal_type
                        log_entry.meal_type = nutritional_data.get("meal_type")
                        
                        # Store synthesis comment as description if not already set
                        synthesis = nutritional_data.get("synthesis_comment", "")
                        if synthesis:
                            log_entry.description = synthesis
                            
                        # Store title
                        title = nutritional_data.get("title")
                        if title:
                            log_entry.title = title
                    
                    await session.commit()
                    logger.info(f"Finalized log {log_id} with status='logged', needs_review={needs_review}")
        except Exception as e:
            logger.error(f"Failed to persist finalized log: {e}")
    
    # Emit final response event
    if log_id:
        yield SSEEvent(
            type=EVENT_RESPONSE,
            payload=AgentResponse(
                log_id=str(log_id),
                nutritional_data=nutritional_data,
                status="logged" if not needs_review else "needs_review",
            ),
        )
    
    yield {
        "needs_review": needs_review,
    }


