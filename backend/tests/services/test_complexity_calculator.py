import pytest

from app.schemas.analysis import AmbiguityLevels
from app.services.complexity_calculator import calculate_complexity
from app.services.food_class_registry import RiskProfile


def test_calculate_complexity_zero_ambiguity():
    """Test baseline case with zero ambiguity."""
    levels = AmbiguityLevels(hidden_ingredients=0, invisible_prep=0, portion_ambiguity=0)
    profile = RiskProfile(
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
    # Wait, the score should probably be normalized or cap at 1.0?
    # The story says "Calculated complexity score (0.0 to 1.0)".
    # But the formula C = Σ(w · L²) + P can easily exceed 1.0 if L is 3.
    # weights are typically small?
    # Let's check the Architecture decision in the story content.
    # "C = (w_i * L_i**2) + ..."
    # If weights are ~0.1 and L is 3, 0.1 * 9 = 0.9.
    # If the score is meant to be 0.0 to 1.0, there must be a normalization step or the weights are very small.
    # Or maybe the formula yields a raw score that is then capped.
    # The schema says "Calculated complexity score (0.0 to 1.0)".
    # I will assume for now that standard weights are such that it fits, or I should cap it at 1.0.
    # Let's assume the result is capped at 1.0.

    levels = AmbiguityLevels(hidden_ingredients=3, invisible_prep=0, portion_ambiguity=0)
    profile = RiskProfile(
        weights={"ingredients": 0.1, "prep": 0.1, "volume": 0.1},
        semantic_penalty=0.0,
        mandatory_clarification=False,
        is_umbrella_term=False,
    )

    # 0.1 * 3^2 = 0.9
    result = calculate_complexity(levels, profile)
    assert result.score == pytest.approx(0.9)
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
        weights={"ingredients": 0.1, "prep": 0.1, "volume": 0.1},
        semantic_penalty=0.2,
        mandatory_clarification=False,
        is_umbrella_term=False,
    )

    result = calculate_complexity(levels, profile)
    assert result.score == pytest.approx(0.7)
    assert result.dominant_factor == "prep"  # 0.4 contribution from prep is highest


def test_calculate_complexity_cap_at_one():
    """Test that complexity score is capped at 1.0."""
    levels = AmbiguityLevels(hidden_ingredients=3, invisible_prep=3, portion_ambiguity=3)
    profile = RiskProfile(
        weights={"ingredients": 0.5, "prep": 0.5, "volume": 0.5},
        semantic_penalty=0.5,
        mandatory_clarification=False,
        is_umbrella_term=False,
    )

    # Needs to cover case where formula > 1.0
    result = calculate_complexity(levels, profile)
    assert result.score == 1.0


def test_calculate_complexity_dominant_factor_tie():
    """Test dominant factor selection when there is a tie."""
    # L_i=2, L_p=2. w_i=0.1, w_p=0.1. Equal contribution 0.4.
    levels = AmbiguityLevels(hidden_ingredients=2, invisible_prep=2, portion_ambiguity=0)
    profile = RiskProfile(
        weights={"ingredients": 0.1, "prep": 0.1, "volume": 0.1},
        semantic_penalty=0.0,
        mandatory_clarification=False,
        is_umbrella_term=False,
    )

    result = calculate_complexity(levels, profile)
    # The logic for tie-breaking isn't strictly specified, but it should be one of them.
    assert result.dominant_factor in ["ingredients", "prep"]
