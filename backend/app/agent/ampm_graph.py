"""AMPM (Automated Multi-Pass Method) subgraph definition.

This module defines the LangGraph subgraph for the AMPM detail cycle.
The subgraph is invoked from the main agent graph when confidence is low.

Graph Structure:
    START -> detail_cycle -> [conditional]
        if all items above threshold OR max_clarifications reached -> [conditional]
            if complexity_score > 0.7 AND detail_cycle inconclusive -> final_probe -> END
            else -> END
        else -> detail_cycle (loop)

Note: AMPM graph logic is mirrored in run_streaming_agent() — keep in sync.
"""

from langgraph.graph import END, START, StateGraph

from app.agent.ampm_nodes import detail_cycle, final_probe
from app.agent.constants import (
    CONFIDENCE_THRESHOLD,
    DETAIL_CYCLE,
    FINAL_PROBE,
    MAX_CLARIFICATIONS,
)
from app.agent.state import AgentState


def _route_after_detail_cycle(state: AgentState) -> str:
    """Route after the detail cycle: loop, probe, or exit."""
    clarification_count = state.get("clarification_count", 0)
    needs_clarification = state.get("needs_clarification", False)

    # If the detail cycle set needs_clarification=True, the user needs to respond
    # before we can loop again. Exit subgraph so the main graph can wait for input.
    if needs_clarification:
        return END

    # Budget exhausted — exit
    if clarification_count >= MAX_CLARIFICATIONS:
        return _route_to_probe_or_exit(state)

    # Check if any items are still low confidence
    nutritional_data = state.get("nutritional_data", {}) or {}
    items = nutritional_data.get("items", [])
    low_items = [item for item in items if item.get("confidence", 1.0) < CONFIDENCE_THRESHOLD]

    if low_items:
        # More items to ask about — loop (but only if budget allows)
        if clarification_count < MAX_CLARIFICATIONS:
            return DETAIL_CYCLE
        return _route_to_probe_or_exit(state)

    # All items above threshold — check if we should do final probe
    return _route_to_probe_or_exit(state)


def _route_to_probe_or_exit(state: AgentState) -> str:
    """Decide whether to do a final probe or exit directly."""
    complexity_score = state.get("complexity_score", 0.0)

    # Only probe if meal is complex AND detail cycle was inconclusive
    nutritional_data = state.get("nutritional_data", {}) or {}
    items = nutritional_data.get("items", [])
    low_items = [item for item in items if item.get("confidence", 1.0) < CONFIDENCE_THRESHOLD]
    inconclusive = len(low_items) > 0

    if complexity_score > 0.7 and inconclusive:
        return FINAL_PROBE

    return END


def get_ampm_graph():
    """
    Build and compile the AMPM subgraph.

    Returns:
        CompiledGraph: The compiled AMPM subgraph ready for integration.
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node(DETAIL_CYCLE, detail_cycle)
    workflow.add_node(FINAL_PROBE, final_probe)

    # Entry: start with detail cycle
    workflow.add_edge(START, DETAIL_CYCLE)

    # Conditional routing after detail cycle
    workflow.add_conditional_edges(
        DETAIL_CYCLE,
        _route_after_detail_cycle,
        {
            DETAIL_CYCLE: DETAIL_CYCLE,
            FINAL_PROBE: FINAL_PROBE,
            END: END,
        },
    )

    # Final probe always exits
    workflow.add_edge(FINAL_PROBE, END)

    return workflow.compile()
