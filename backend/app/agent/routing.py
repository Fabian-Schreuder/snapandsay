"""Confidence-based routing logic for the agent graph."""

from app.agent.constants import (
    CONFIDENCE_THRESHOLD,
    FINALIZE_LOG,
    GENERATE_CLARIFICATION,
    MAX_CLARIFICATIONS,
)
from app.agent.state import AgentState


def route_by_confidence(state: AgentState) -> str:
    """
    Route agent based on overall confidence score.

    This function implements the probabilistic silence pattern:
    - High confidence (>= 0.85) -> Skip clarification, go to finalize
    - Low confidence (< 0.85) -> Ask clarification question
    - Max attempts reached (>= 2) -> Force finalize with review flag

    Args:
        state: Current agent state with overall_confidence and clarification_count

    Returns:
        Node name to route to: FINALIZE_LOG or GENERATE_CLARIFICATION
    """
    clarification_count = state.get("clarification_count", 0)
    overall_confidence = state.get("overall_confidence", 0.0)

    # Guard: Max clarification attempts reached
    if clarification_count >= MAX_CLARIFICATIONS:
        return FINALIZE_LOG

    # Route based on confidence threshold
    if overall_confidence >= CONFIDENCE_THRESHOLD:
        return FINALIZE_LOG

    return GENERATE_CLARIFICATION
