import pytest
from pydantic import ValidationError

from app.schemas.analysis import AmbiguityLevels, AnalysisResult, ComplexityBreakdown, FoodItem


def test_ambiguity_levels_validation():
    """Test that AmbiguityLevels validates 0-3 range."""
    # Valid
    levels = AmbiguityLevels(hidden_ingredients=0, invisible_prep=3, portion_ambiguity=1)
    assert levels.hidden_ingredients == 0
    assert levels.invisible_prep == 3
    assert levels.portion_ambiguity == 1

    # Invalid - too high
    with pytest.raises(ValidationError):
        AmbiguityLevels(hidden_ingredients=4, invisible_prep=0, portion_ambiguity=0)

    # Invalid - too low
    with pytest.raises(ValidationError):
        AmbiguityLevels(hidden_ingredients=-1, invisible_prep=0, portion_ambiguity=0)


def test_complexity_breakdown_creation():
    """Test creating a ComplexityBreakdown object."""
    levels = AmbiguityLevels(hidden_ingredients=1, invisible_prep=1, portion_ambiguity=1)
    breakdown = ComplexityBreakdown(
        levels=levels,
        weights={"hidden": 0.4},
        semantic_penalty=0.1,
        dominant_factor="hidden_ingredients",
        score=0.5,
    )
    assert breakdown.levels == levels
    assert breakdown.score == 0.5
    assert breakdown.dominant_factor == "hidden_ingredients"


def test_analysis_result_with_breakdown():
    """Test AnalysisResult with the new complexity_breakdown field."""
    levels = AmbiguityLevels(hidden_ingredients=2, invisible_prep=2, portion_ambiguity=2)
    breakdown = ComplexityBreakdown(levels=levels, score=0.8)

    result = AnalysisResult(
        title="Test Meal",
        items=[FoodItem(name="Test", quantity="1", confidence=0.9)],
        synthesis_comment="Test comment",
        complexity_score=0.8,
        complexity_breakdown=breakdown,
    )

    assert result.complexity_score == 0.8
    assert result.complexity_breakdown is not None
    assert result.complexity_breakdown.levels.hidden_ingredients == 2
