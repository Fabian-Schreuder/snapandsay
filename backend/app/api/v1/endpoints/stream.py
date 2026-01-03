"""SSE streaming endpoint for agent analysis."""

import asyncio
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.agent.constants import EVENT_ERROR, EVENT_RESPONSE
from app.agent.graph import run_streaming_agent
from app.agent.state import AgentState
from app.api import deps
from app.schemas.sse import AgentError, AgentResponse, SSEEvent
from app.schemas.stream import StreamAnalysisRequest
from app.services.streaming_service import format_sse, format_sse_comment

logger = logging.getLogger(__name__)

router = APIRouter()

# Processing timeout in seconds
PROCESSING_TIMEOUT = 60
# Heartbeat interval in seconds
HEARTBEAT_INTERVAL = 15


async def event_generator(
    request: StreamAnalysisRequest, token: str | None = None
) -> AsyncGenerator[str, None]:
    """
    Generate SSE events from the agent processing.

    Args:
        request: The stream analysis request.

    Yields:
        SSE-formatted strings.
    """
    initial_state: AgentState = {
        "messages": [],
        "image_url": request.image_path,
        "audio_url": request.audio_path,
        "nutritional_data": None,
        "user_token": token,
        "log_id": request.log_id,
    }

    last_heartbeat = asyncio.get_event_loop().time()
    final_nutritional_data = None

    try:
        # Wrap the generator with timeout context manager
        async with asyncio.timeout(PROCESSING_TIMEOUT):
            async for item in run_streaming_agent(initial_state):
                current_time = asyncio.get_event_loop().time()

                # Send heartbeat if needed
                if current_time - last_heartbeat > HEARTBEAT_INTERVAL:
                    yield await format_sse_comment("heartbeat")
                    last_heartbeat = current_time

                if isinstance(item, SSEEvent):
                    yield await format_sse(item)

                    # Check for errors - stop processing if error occurred
                    if item.type == EVENT_ERROR:
                        return
                else:
                    # This is the final state dict
                    final_nutritional_data = item.get("nutritional_data")

        # Emit final response event
        if final_nutritional_data:
            response_event = SSEEvent(
                type=EVENT_RESPONSE,
                payload=AgentResponse(
                    log_id=str(request.log_id),
                    nutritional_data=final_nutritional_data,
                    status="success",
                ),
            )
            yield await format_sse(response_event)
        else:
            # No nutritional data - emit error
            error_event = SSEEvent(
                type=EVENT_ERROR,
                payload=AgentError(
                    code="NO_RESULT",
                    message="I wasn't able to analyze your meal. Please try again.",
                ),
            )
            yield await format_sse(error_event)

    except TimeoutError:
        logger.error(f"Agent processing timed out after {PROCESSING_TIMEOUT}s")
        error_event = SSEEvent(
            type=EVENT_ERROR,
            payload=AgentError(
                code="TIMEOUT",
                message="Processing took too long. Please try again.",
            ),
        )
        yield await format_sse(error_event)

    except Exception as e:
        logger.error(f"Agent processing error: {e}")
        error_event = SSEEvent(
            type=EVENT_ERROR,
            payload=AgentError(
                code="INTERNAL_ERROR",
                message="Something went wrong. Please try again.",
            ),
        )
        yield await format_sse(error_event)


@router.post("/stream")
async def stream_analysis(
    request: StreamAnalysisRequest,
    current_user: deps.UserContext = Depends(deps.get_current_user),
    token: str = Depends(deps.oauth2_scheme),
) -> StreamingResponse:
    """
    Stream agent analysis results via Server-Sent Events.

    This endpoint accepts a log_id (from a previous upload) and optional
    file paths, then streams the agent's processing as SSE events.

    Event types:
    - agent.thought: Intermediate processing updates
    - agent.response: Final analysis result
    - agent.error: Error during processing

    Returns:
        StreamingResponse with media_type text/event-stream
    """
    return StreamingResponse(
        event_generator(request, token),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
