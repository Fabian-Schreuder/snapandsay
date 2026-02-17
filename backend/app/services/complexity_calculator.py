from app.schemas.analysis import AmbiguityLevels, ComplexityBreakdown
from app.services.food_class_registry import RiskProfile


def calculate_complexity(ambiguity_levels: AmbiguityLevels, risk_profile: RiskProfile) -> ComplexityBreakdown:
    """
    Calculates the detailed complexity breakdown using the formula:
    C = Σ(w · L²) + P
    """
    # 1. Calculate weighted contributions for each dimension
    # Note: weights in risk_profile are like {"ingredients": 0.5, ...}
    # AmbiguityLevels has fields: hidden_ingredients, invisible_prep, portion_ambiguity

    # Map dimensions to their corresponding level value and weight key
    # Dimension name -> (level value, weight key)
    dimensions = {
        "ingredients": (ambiguity_levels.hidden_ingredients, "ingredients"),
        "prep": (ambiguity_levels.invisible_prep, "prep"),
        "volume": (ambiguity_levels.portion_ambiguity, "volume"),
    }

    contributions = {}
    for dim, (level, weight_key) in dimensions.items():
        weight = risk_profile.weights.get(weight_key, 0.0)
        # Contribution = w * L^2
        contribution = weight * (level**2)
        contributions[dim] = contribution

    # 2. Sum contributions and add semantic penalty
    sum_weighted_squares = sum(contributions.values())
    raw_score = sum_weighted_squares + risk_profile.semantic_penalty

    # 3. Cap score at 1.0
    final_score = min(raw_score, 1.0)

    # 4. Determine dominant factor (the dimension with the largest w·L² contribution).
    # Only considers the 3 ambiguity dimensions, not the semantic penalty.
    dominant_factor = None
    if final_score > 0:
        max_contribution = -1.0
        for dim, contrib in contributions.items():
            if contrib > max_contribution:
                max_contribution = contrib
                dominant_factor = dim

        if max_contribution == 0.0:
            dominant_factor = None

    return ComplexityBreakdown(
        levels=ambiguity_levels,
        weights=risk_profile.weights,
        semantic_penalty=risk_profile.semantic_penalty,
        dominant_factor=dominant_factor,
        score=final_score,
    )
