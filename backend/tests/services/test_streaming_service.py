"""Tests for the streaming service."""
import pytest
from datetime import datetime

from app.services.streaming_service import format_sse, format_sse_comment
from app.schemas.sse import SSEEvent, AgentThought, AgentResponse, AgentError


@pytest.mark.asyncio
async def test_format_sse_thought_event():
    """Test format_sse produces valid SSE format for thought events."""
    thought = AgentThought(
        step="analyzing",
        message="Looking at your meal...",
        timestamp=datetime(2025, 12, 7, 12, 0, 0),
    )
    event = SSEEvent(type="agent.thought", payload=thought)

    result = await format_sse(event)

    # Should start with "data: " and end with double newline
    assert result.startswith("data: ")
    assert result.endswith("\n\n")

    # Should contain valid JSON
    import json

    json_str = result[6:-2]  # Remove "data: " prefix and "\n\n" suffix
    parsed = json.loads(json_str)
    assert parsed["type"] == "agent.thought"
    assert parsed["payload"]["step"] == "analyzing"
    assert parsed["payload"]["message"] == "Looking at your meal..."


@pytest.mark.asyncio
async def test_format_sse_response_event():
    """Test format_sse produces valid SSE format for response events."""
    response = AgentResponse(
        log_id="123e4567-e89b-12d3-a456-426614174000",
        nutritional_data={"calories": 500, "protein": 25},
        status="success",
    )
    event = SSEEvent(type="agent.response", payload=response)

    result = await format_sse(event)

    assert result.startswith("data: ")
    assert result.endswith("\n\n")

    import json

    json_str = result[6:-2]
    parsed = json.loads(json_str)
    assert parsed["type"] == "agent.response"
    assert parsed["payload"]["log_id"] == "123e4567-e89b-12d3-a456-426614174000"
    assert parsed["payload"]["nutritional_data"]["calories"] == 500


@pytest.mark.asyncio
async def test_format_sse_error_event():
    """Test format_sse produces valid SSE format for error events."""
    error = AgentError(
        code="PROCESSING_ERROR",
        message="I'm having trouble analyzing your image.",
    )
    event = SSEEvent(type="agent.error", payload=error)

    result = await format_sse(event)

    assert result.startswith("data: ")
    assert result.endswith("\n\n")

    import json

    json_str = result[6:-2]
    parsed = json.loads(json_str)
    assert parsed["type"] == "agent.error"
    assert parsed["payload"]["code"] == "PROCESSING_ERROR"


@pytest.mark.asyncio
async def test_format_sse_comment():
    """Test format_sse_comment produces valid SSE comment format."""
    result = await format_sse_comment("heartbeat")

    # Should start with ": " and end with double newline
    assert result == ": heartbeat\n\n"


@pytest.mark.asyncio
async def test_format_sse_comment_empty():
    """Test format_sse_comment with empty string."""
    result = await format_sse_comment("")

    assert result == ": \n\n"
