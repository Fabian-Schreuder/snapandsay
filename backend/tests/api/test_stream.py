"""Tests for the SSE streaming endpoint."""
from unittest.mock import patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.agent.constants import EVENT_ERROR, EVENT_THOUGHT
from app.schemas.sse import AgentError, AgentThought, SSEEvent


@pytest.mark.asyncio
async def test_stream_endpoint_returns_sse_content_type(test_client: AsyncClient):
    """Test that the stream endpoint returns proper SSE content-type header."""
    request_data = {
        "log_id": str(uuid4()),
        "image_path": "https://example.com/image.jpg",
    }

    with patch("app.api.v1.endpoints.stream.run_streaming_agent") as mock_agent:
        # Make it an async generator that yields a single thought and final state
        async def mock_generator(*args):
            yield SSEEvent(
                type=EVENT_THOUGHT,
                payload=AgentThought(step="analyzing", message="Looking..."),
            )
            yield {"nutritional_data": {"items": [], "synthesis_comment": "Test"}}

        mock_agent.return_value = mock_generator()

        response = await test_client.post("/api/v1/analysis/stream", json=request_data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        assert response.headers["cache-control"] == "no-cache"


@pytest.mark.asyncio
async def test_stream_endpoint_event_format(test_client: AsyncClient):
    """Test that SSE events are formatted correctly."""
    request_data = {
        "log_id": str(uuid4()),
        "image_path": "https://example.com/image.jpg",
    }

    with patch("app.api.v1.endpoints.stream.run_streaming_agent") as mock_agent:
        async def mock_generator(*args):
            yield SSEEvent(
                type=EVENT_THOUGHT,
                payload=AgentThought(step="analyzing", message="Looking at your meal..."),
            )
            yield {"nutritional_data": {"items": [], "synthesis_comment": "Test"}}

        mock_agent.return_value = mock_generator()

        response = await test_client.post("/api/v1/analysis/stream", json=request_data)

        content = response.text
        
        # Should contain "data: " prefix
        assert "data: " in content
        # Should contain event type
        assert "agent.thought" in content


@pytest.mark.asyncio
async def test_stream_endpoint_emits_error_event(test_client: AsyncClient):
    """Test that errors emit agent.error events."""
    request_data = {
        "log_id": str(uuid4()),
        "image_path": "https://example.com/image.jpg",
    }

    with patch("app.api.v1.endpoints.stream.run_streaming_agent") as mock_agent:
        async def mock_generator(*args):
            yield SSEEvent(
                type=EVENT_ERROR,
                payload=AgentError(code="TEST_ERROR", message="Test error"),
            )

        mock_agent.return_value = mock_generator()

        response = await test_client.post("/api/v1/analysis/stream", json=request_data)

        content = response.text
        assert "agent.error" in content
        assert "TEST_ERROR" in content


@pytest.mark.asyncio
async def test_stream_endpoint_emits_response_on_success(test_client: AsyncClient):
    """Test that successful processing emits agent.response event."""
    request_data = {
        "log_id": str(uuid4()),
        "image_path": "https://example.com/image.jpg",
    }

    with patch("app.api.v1.endpoints.stream.run_streaming_agent") as mock_agent:
        async def mock_generator(*args):
            yield {"nutritional_data": {"items": [{"name": "apple"}], "synthesis_comment": "Found an apple"}}

        mock_agent.return_value = mock_generator()

        response = await test_client.post("/api/v1/analysis/stream", json=request_data)

        content = response.text
        assert "agent.response" in content
        assert "success" in content
