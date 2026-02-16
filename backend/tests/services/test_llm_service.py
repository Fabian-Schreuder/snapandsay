"""Tests for LLMService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.analysis import AmbiguityLevels, AnalysisResult, ComplexityBreakdown, FoodItem
from app.services.llm_service import LLMGenerationError, analyze_multimodal


@pytest.mark.asyncio
async def test_analyze_multimodal_success():
    """Test successful multimodal analysis."""
    mock_result = AnalysisResult(
        title="Apple",
        items=[
            FoodItem(name="Apple", quantity="1", calories=95, confidence=0.99),
        ],
        synthesis_comment="Healthy snack.",
        complexity_score=0.1,
        complexity_breakdown=ComplexityBreakdown(
            levels=AmbiguityLevels(hidden_ingredients=0, invisible_prep=0, portion_ambiguity=0),
            score=0.1,
            dominant_factor="none",
        ),
    )

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.parsed = mock_result
    mock_response.choices[0].message.refusal = None

    mock_client = MagicMock()
    mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_response)

    with patch("app.services.llm_service._get_openai_client", return_value=mock_client):
        result = await analyze_multimodal(
            image_url="http://test.com/image.jpg", transcript="A red apple", provider="openai"
        )

        assert result == mock_result
        mock_client.beta.chat.completions.parse.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_multimodal_no_inputs():
    """Test that ValueError is raised when no inputs provided."""
    with pytest.raises(ValueError, match="No input provided"):
        await analyze_multimodal(image_url=None, transcript=None)


@pytest.mark.asyncio
async def test_analyze_multimodal_api_error():
    """Test that LLMGenerationError is raised on API failure."""
    mock_client = MagicMock()
    mock_client.beta.chat.completions.parse = AsyncMock(side_effect=Exception("API Error"))

    with patch("app.services.llm_service._get_openai_client", return_value=mock_client):
        with pytest.raises(LLMGenerationError, match="Failed to analyze input"):
            await analyze_multimodal(image_url="http://test.com/image.jpg", provider="openai")
