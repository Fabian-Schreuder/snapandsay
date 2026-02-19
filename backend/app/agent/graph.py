from collections.abc import AsyncGenerator

from langgraph.graph import END, START, StateGraph

from app.agent.ampm_graph import get_ampm_graph
from app.agent.ampm_nodes import (
    detail_cycle_streaming,
    final_probe_streaming,
)
from app.agent.constants import (
    AMPM_ENTRY,
    ANALYZE_INPUT,
    FINALIZE_LOG,
)
from app.agent.nodes import (
    analyze_input,
    analyze_input_streaming,
    finalize_log,
    finalize_log_streaming,
)
from app.agent.routing import route_by_confidence
from app.agent.state import AgentState
from app.schemas.sse import SSEEvent


def get_agent_graph():
    """
    Initialize and compile the agent graph with conditional routing.

    Graph Structure:
        START -> analyze_input -> [conditional edge]
            if confidence >= 0.85 or max_attempts: -> finalize_log -> END
            else: -> ampm_entry (subgraph) -> finalize_log -> END

    Note: AMPM streaming logic mirrored in run_streaming_agent() — keep in sync.
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node(ANALYZE_INPUT, analyze_input)
    workflow.add_node(AMPM_ENTRY, get_ampm_graph())  # AMPM subgraph
    workflow.add_node(FINALIZE_LOG, finalize_log)

    # Entry point
    workflow.add_edge(START, ANALYZE_INPUT)

    # Conditional routing based on confidence
    workflow.add_conditional_edges(
        ANALYZE_INPUT,
        route_by_confidence,
        {
            AMPM_ENTRY: AMPM_ENTRY,
            FINALIZE_LOG: FINALIZE_LOG,
        },
    )

    # AMPM subgraph leads to finalize
    workflow.add_edge(AMPM_ENTRY, FINALIZE_LOG)
    workflow.add_edge(FINALIZE_LOG, END)

    # Compile the graph
    app = workflow.compile()
    return app


async def run_streaming_agent(
    initial_state: AgentState,
) -> AsyncGenerator[SSEEvent | dict, None]:
    """
    Run the agent graph with streaming SSE events and conditional routing.

    This function executes the agent nodes in sequence, yielding
    SSE events as each node processes. Routing is based on confidence:
    - High confidence (>= 0.85): analyze -> finalize
    - Low confidence (< 0.85): analyze -> AMPM detail cycle -> finalize

    Note: AMPM graph logic mirrored in get_agent_graph() — keep in sync.

    Args:
        initial_state: The initial agent state with image_url/audio_url.

    Yields:
        SSEEvent objects during processing.
        Final dict with the complete state update when done.
    """
    state = dict(initial_state)

    # Run analyze_input_streaming
    async for item in analyze_input_streaming(state):
        if isinstance(item, SSEEvent):
            yield item
        else:
            # State update
            state.update(item)

    # Determine routing based on confidence
    needs_clarification = False

    # Route conditionally using centralized logic
    if route_by_confidence(state) == AMPM_ENTRY:
        # Low confidence — run AMPM detail cycle (streaming)
        async for item in detail_cycle_streaming(state):
            if isinstance(item, SSEEvent):
                yield item
            else:
                state.update(item)
                if item.get("needs_clarification"):
                    needs_clarification = True

        # After detail cycle, conditionally run final probe
        if not needs_clarification:
            async for item in final_probe_streaming(state):
                if isinstance(item, SSEEvent):
                    yield item
                else:
                    state.update(item)
                    if item.get("needs_clarification"):
                        needs_clarification = True

    # Run finalize only if no clarification needed
    if not needs_clarification:
        async for item in finalize_log_streaming(state):
            if isinstance(item, SSEEvent):
                yield item
            else:
                state.update(item)

    # Final state is available in state dict
    yield state
