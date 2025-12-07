from typing import AsyncGenerator
from datetime import datetime

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
)
from app.schemas.sse import SSEEvent, AgentThought, AgentResponse, AgentError
import logging

logger = logging.getLogger(__name__)


async def analyze_input(state: AgentState) -> dict:
    """
    Analyze the input (image or text) to determine the next step.
    """
    image_url = state.get("image_url")
    audio_url = state.get("audio_url")
    transcript = None
    
    if audio_url:
        logger.info(f"Transcribing audio from {audio_url}")
        try:
            transcript = await voice_service.transcribe_audio(audio_url)
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            raise e
            
    if not image_url and not transcript:
        logger.warning("No input provided for analysis")
        return {}
        
    logger.info("Analyzing multimodal input")
    try:
        result = await llm_service.analyze_multimodal(image_url=image_url, transcript=transcript)
        return {"nutritional_data": result.model_dump()}
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise e


async def analyze_input_streaming(
    state: AgentState,
) -> AsyncGenerator[SSEEvent | dict, None]:
    """
    Analyze input with streaming SSE events.

    Yields SSEEvent objects during processing, and finally yields
    the state update dict with nutritional_data.
    """
    image_url = state.get("image_url")
    audio_url = state.get("audio_url")
    transcript = None

    # Emit start thought
    yield SSEEvent(
        type=EVENT_THOUGHT,
        payload=AgentThought(
            step=STEP_ANALYZING,
            message=MSG_ANALYZING_START,
            timestamp=datetime.utcnow(),
        ),
    )

    if audio_url:
        logger.info(f"Transcribing audio from {audio_url}")
        try:
            transcript = await voice_service.transcribe_audio(audio_url)
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
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

    async def on_token(token: str) -> None:
        nonlocal token_count
        token_count += 1
        # Emit progress thoughts periodically (every ~10 tokens)
        if token_count % 10 == 0:
            # Note: We yield from the main generator, not here
            pass

    try:
        # Emit tokens thought
        yield SSEEvent(
            type=EVENT_THOUGHT,
            payload=AgentThought(
                step=STEP_ANALYZING,
                message=MSG_ANALYZING_TOKENS,
                timestamp=datetime.utcnow(),
            ),
        )

        result = await llm_service.analyze_multimodal_streaming(
            image_url=image_url, transcript=transcript, on_token=on_token
        )

        # Emit completion thought
        yield SSEEvent(
            type=EVENT_THOUGHT,
            payload=AgentThought(
                step=STEP_ANALYZING,
                message=MSG_ANALYZING_COMPLETE,
                timestamp=datetime.utcnow(),
            ),
        )

        # Yield the state update
        yield {"nutritional_data": result.model_dump()}

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        yield SSEEvent(
            type=EVENT_ERROR,
            payload=AgentError(
                code="ANALYSIS_ERROR",
                message="I'm having trouble analyzing your meal. Please try again.",
            ),
        )


async def generate_clarification(state: AgentState) -> dict:
    """
    Generate a clarification question if the input is ambiguous.
    This is a placeholder implementation.
    """
    return {}


async def generate_clarification_streaming(
    state: AgentState,
) -> AsyncGenerator[SSEEvent | dict, None]:
    """Generate clarification with streaming events."""
    yield SSEEvent(
        type=EVENT_THOUGHT,
        payload=AgentThought(
            step=STEP_CLARIFYING,
            message=MSG_CLARIFYING,
            timestamp=datetime.utcnow(),
        ),
    )
    # Placeholder - actual clarification logic would go here
    yield {}


async def finalize_log(state: AgentState) -> dict:
    """
    Finalize the log entry after sufficient information has been gathered.
    This is a placeholder implementation.
    """
    return {}


async def finalize_log_streaming(
    state: AgentState,
) -> AsyncGenerator[SSEEvent | dict, None]:
    """Finalize log with streaming events."""
    yield SSEEvent(
        type=EVENT_THOUGHT,
        payload=AgentThought(
            step=STEP_FINALIZING,
            message=MSG_FINALIZING,
            timestamp=datetime.utcnow(),
        ),
    )
    # Placeholder - actual finalization logic would go here
    yield {}

