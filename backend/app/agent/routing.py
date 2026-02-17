"""Confidence-based routing logic for the agent graph."""

from app.agent.constants import (
    AMPM_ENTRY,
    CONFIDENCE_THRESHOLD,
    FINALIZE_LOG,
    MAX_CLARIFICATIONS,
)
from app.agent.state import AgentState


def route_by_confidence(state: AgentState) -> str:
    """
    Route agent based on overall confidence score.

    This function implements the probabilistic silence pattern:
    - High confidence (>= 0.85) -> Skip clarification, go to finalize
    - Low confidence (< 0.85) -> Enter AMPM subgraph for detail cycle
    - Max attempts reached (>= 2) -> Force finalize with review flag

    Args:
        state: Current agent state with overall_confidence and clarification_count

    Returns:
        Node name to route to: FINALIZE_LOG or AMPM_ENTRY
    """
    clarification_count = state.get("clarification_count", 0)
    overall_confidence = state.get("overall_confidence", 0.0)

    # Guard: Max clarification attempts reached
    if clarification_count >= MAX_CLARIFICATIONS:
        return FINALIZE_LOG

    # 1. Mandatory Override
    if state.get("mandatory_clarification"):
        return AMPM_ENTRY

    # 2. Clinical Threshold Override
    # Score range: 0.0-1.0.  Default threshold 15.0 effectively disables
    # clinical routing for standard users (score can never exceed 1.0).
    # Diabetic profile example: threshold=0.5, score=0.8 → triggers AMPM.
    score = state.get("complexity_score", 0.0)
    threshold = state.get("clinical_threshold", 15.0)

    if score > threshold:
        return AMPM_ENTRY

    # 3. Standard Confidence Check (Existing)
    if overall_confidence >= CONFIDENCE_THRESHOLD:
        return FINALIZE_LOG

    return AMPM_ENTRY
