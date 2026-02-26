import pytest

from app.schemas.analysis import AmbiguityLevels
from app.services.complexity_calculator import calculate_complexity
from app.services.food_class_registry import RiskProfile


def test_calculate_complexity_zero_ambiguity():
    """Test baseline case with zero ambiguity."""
    levels = AmbiguityLevels(hidden_ingredients=0, invisible_prep=0, portion_ambiguity=0)
    profile = RiskProfile(
        name="test",
        weights={"ingredients": 0.5, "prep": 0.5, "volume": 0.5},
        semantic_penalty=0.0,
        mandatory_clarification=False,
        is_umbrella_term=False,
    )

    result = calculate_complexity(levels, profile)

    assert result.score == 0.0
    assert result.dominant_factor is None
    assert result.semantic_penalty == 0.0


def test_calculate_complexity_high_ambiguity_single_dimension():
    """Test high ambiguity in a single dimension."""
    # L_i = 3, others 0. w_i = 0.5
    # Score = 0.5 * 3^2 = 0.5 * 9 = 4.5
    levels = AmbiguityLevels(hidden_ingredients=3, invisible_prep=0, portion_ambiguity=0)
    profile = RiskProfile(
        name="test",
        weights={"ingredients": 0.5, "prep": 0.1, "volume": 0.1},
        semantic_penalty=0.0,
        mandatory_clarification=False,
        is_umbrella_term=False,
    )

    result = calculate_complexity(levels, profile)
    assert result.score == pytest.approx(4.5)
    assert result.dominant_factor == "ingredients"


def test_calculate_complexity_mixed_ambiguity_with_penalty():
    """Test mixed ambiguity levels with semantic penalty."""
    # L_i=1, L_p=2, L_v=0
    # w_i=0.1, w_p=0.1, w_v=0.1
    # P=0.2
    # C = (0.1 * 1^2) + (0.1 * 2^2) + 0 + 0.2
    # C = 0.1 + 0.4 + 0.2 = 0.7

    levels = AmbiguityLevels(hidden_ingredients=1, invisible_prep=2, portion_ambiguity=0)
    profile = RiskProfile(
        name="test",
        weights={"ingredients": 0.1, "prep": 0.1, "volume": 0.1},
        semantic_penalty=0.2,
        mandatory_clarification=False,
        is_umbrella_term=False,
    )

    result = calculate_complexity(levels, profile)
    assert result.score == pytest.approx(0.7)
    assert result.dominant_factor == "prep"  # 0.4 contribution from prep is highest


def test_calculate_complexity_unbounded():
    """Test that complexity score can exceed 1.0 (unbounded)."""
    levels = AmbiguityLevels(hidden_ingredients=3, invisible_prep=3, portion_ambiguity=3)
    profile = RiskProfile(
        name="test",
        weights={"ingredients": 0.5, "prep": 0.5, "volume": 0.5},
        semantic_penalty=0.5,
        mandatory_clarification=False,
        is_umbrella_term=False,
    )

    # 1.5 * 9 = 13.5. Plus 0.5 penalty = 14.0
    result = calculate_complexity(levels, profile)
    assert result.score == 14.0


def test_calculate_complexity_dominant_factor_tie():
    """Test dominant factor selection when there is a tie."""
    # L_i=2, L_p=2. w_i=0.1, w_p=0.1. Equal contribution 0.4.
    levels = AmbiguityLevels(hidden_ingredients=2, invisible_prep=2, portion_ambiguity=0)
    profile = RiskProfile(
        name="test",
        weights={"ingredients": 0.1, "prep": 0.1, "volume": 0.1},
        semantic_penalty=0.0,
        mandatory_clarification=False,
        is_umbrella_term=False,
    )

    result = calculate_complexity(levels, profile)
    # The logic for tie-breaking isn't strictly specified, but it should be one of them.
    assert result.dominant_factor in ["ingredients", "prep"]
