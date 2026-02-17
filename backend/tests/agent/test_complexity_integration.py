from unittest.mock import AsyncMock, patch

import pytest

from app.agent.nodes import analyze_input
from app.schemas.analysis import AmbiguityLevels, AnalysisResult, ComplexityBreakdown, FoodItem
from app.services.food_class_registry import RiskProfile


@pytest.mark.asyncio
async def test_analyze_input_calculates_complexity():
    """
    Test that analyze_input correctly enriches the result with deterministic complexity score.
    """
    # 1. Setup Mock State
    state = {
        "image_url": "http://example.com/image.jpg",
        "user_token": "test-token",
        "start_time": 1234567890.0,
        "provider": "openai",
        "model": "gpt-4-vision-preview",
    }

    # 2. Setup Mock LLM Result
    mock_levels = AmbiguityLevels(hidden_ingredients=2, invisible_prep=2, portion_ambiguity=0)
    # Initially score=0.0 because LLM doesn't calculate it deterministically
    mock_breakdown = ComplexityBreakdown(
        levels=mock_levels, weights={}, semantic_penalty=0.0, dominant_factor=None, score=0.0
    )

    mock_analysis_result = AnalysisResult(
        title="Test Meal",
        items=[FoodItem(name="Test Food", quantity="1 serving", confidence=0.9)],
        synthesis_comment="Looks good",
        complexity_breakdown=mock_breakdown,
        complexity_score=0.0,
    )

    # 3. Setup Mocks
    with patch("app.services.llm_service.analyze_multimodal", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_analysis_result

        with patch("app.agent.nodes.food_registry") as mock_registry:
            # Mock Registry Behavior
            # When looking up "Test Meal" or "Test Food", return a known high-risk profile
            mock_registry.lookup.return_value = "high_risk_class"

            mock_profile = RiskProfile(
                weights={"ingredients": 0.5, "prep": 0.5, "volume": 0.5},
                semantic_penalty=0.1,
                mandatory_clarification=False,
                is_umbrella_term=False,
            )
            mock_registry.get_risk_profile.return_value = mock_profile

            # 4. Call Function
            result = await analyze_input(state)

            # 5. Assertions

            # Verify LLM service called
            mock_analyze.assert_called_once()

            # Verify Result contains calculated complexity
            # Calculation:
            # L_i=2, L_p=2, L_v=0
            # w=0.5
            # C = 0.5*(2^2) + 0.5*(2^2) + 0 + 0.1 = 0.5*4 + 0.5*4 + 0.1 = 2.0 + 2.0 + 0.1 = 4.1
            # Capped at 1.0

            assert "complexity_breakdown" in result
            breakdown = result["complexity_breakdown"]

            assert breakdown.score == 1.0
            assert result["complexity_score"] == 1.0
            assert breakdown.dominant_factor == "ingredients" or breakdown.dominant_factor == "prep"

            # Verify weights were populated from registry
            assert breakdown.weights == mock_profile.weights
            assert breakdown.semantic_penalty == mock_profile.semantic_penalty


@pytest.mark.asyncio
async def test_analyze_input_handles_missing_breakdown():
    """
    Test fallback when LLM doesn't return breakdown (e.g. failure or old model).
    """
    state = {"image_url": "http://example.com/image.jpg"}

    mock_analysis_result = AnalysisResult(
        title="Simple Meal",
        items=[],
        synthesis_comment="Simple",
        complexity_breakdown=None,  # Missing
        complexity_score=0.5,  # Legacy score
    )

    with patch("app.services.llm_service.analyze_multimodal", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_analysis_result

        # Should not crash
        result = await analyze_input(state)

        # Complexity score should remain untouched
        assert result["complexity_score"] == 0.5
        assert result["complexity_breakdown"] is None


@pytest.mark.asyncio
async def test_analyze_input_uses_default_profile_when_no_registry_match():
    """
    Test that _enrich_with_complexity falls back to the default risk profile
    when food_registry.lookup returns None for all items (M2 fix).
    """
    state = {
        "image_url": "http://example.com/image.jpg",
        "user_token": "test-token",
        "start_time": 1234567890.0,
        "provider": "openai",
        "model": "gpt-4-vision-preview",
    }

    mock_levels = AmbiguityLevels(hidden_ingredients=1, invisible_prep=1, portion_ambiguity=0)
    mock_breakdown = ComplexityBreakdown(
        levels=mock_levels, weights={}, semantic_penalty=0.0, dominant_factor=None, score=0.0
    )

    mock_analysis_result = AnalysisResult(
        title="Unknown Dish",
        items=[FoodItem(name="Mystery Food", quantity="1 serving", confidence=0.9)],
        synthesis_comment="Something",
        complexity_breakdown=mock_breakdown,
        complexity_score=0.0,
    )

    default_profile = RiskProfile(
        weights={"ingredients": 0.1, "prep": 0.1, "volume": 0.1},
        semantic_penalty=0.0,
        mandatory_clarification=False,
        is_umbrella_term=False,
    )

    with patch("app.services.llm_service.analyze_multimodal", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_analysis_result

        with patch("app.agent.nodes.food_registry") as mock_registry:
            # No matches in registry
            mock_registry.lookup.return_value = None
            mock_registry.get_risk_profile.return_value = default_profile

            result = await analyze_input(state)

            # Should still calculate complexity using default profile
            # C = 0.1*(1²) + 0.1*(1²) + 0 + 0 = 0.2
            assert result["complexity_breakdown"].score == pytest.approx(0.2)
            assert result["complexity_score"] == pytest.approx(0.2)

            # get_risk_profile should be called with "" (empty string) for default fallback
            mock_registry.get_risk_profile.assert_called_once_with("")
