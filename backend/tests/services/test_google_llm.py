"""Tests for Google LLM integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.analysis import AnalysisResult, FoodItem
from app.services.llm_service import analyze_multimodal, analyze_multimodal_streaming


@pytest.mark.asyncio
async def test_analyze_multimodal_google_success():
    """Test successful Google Gemini analysis."""
    mock_result = AnalysisResult(
        title="Banana",
        items=[
            FoodItem(name="Banana", quantity="1", calories=105, confidence=0.98),
        ],
        synthesis_comment="Good source of potassium.",
    )

    mock_response = MagicMock()
    mock_response.text = mock_result.model_dump_json()

    mock_client = MagicMock()
    # Mock the aio.models.generate_content method as an async function
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with patch("app.services.llm_service._get_google_client", return_value=mock_client):
        result = await analyze_multimodal(
            image_url="http://test.com/banana.jpg", transcript="A yellow banana", provider="google"
        )

        assert result == mock_result
        mock_client.aio.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_multimodal_google_streaming_success():
    """Test successful Google Gemini streaming analysis."""
    mock_result = AnalysisResult(
        title="Orange",
        items=[
            FoodItem(name="Orange", quantity="1", calories=60, confidence=0.97),
        ],
        synthesis_comment="Vitamins!",
    )

    # Mock stream chunks
    mock_chunk1 = MagicMock()
    mock_chunk1.text = '{"title": "Orange", "items": [{"name": "Orange", "quantity": "1", '
    mock_chunk2 = MagicMock()
    mock_chunk2.text = '"calories": 60, "confidence": 0.97}], "synthesis_comment": "Vitamins!"}'

    async def mock_stream(*args, **kwargs):
        yield mock_chunk1
        yield mock_chunk2

    mock_client = MagicMock()
    mock_client.aio.models.generate_content_stream = MagicMock(return_value=mock_stream())

    with patch("app.services.llm_service._get_google_client", return_value=mock_client):
        tokens = []

        async def on_token(token: str):
            tokens.append(token)

        result = await analyze_multimodal_streaming(
            image_url="http://test.com/orange.jpg", on_token=on_token, provider="google"
        )

        assert result == mock_result
        assert len(tokens) == 2
