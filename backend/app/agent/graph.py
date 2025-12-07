from typing import AsyncGenerator
from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState
from app.agent.nodes import (
    analyze_input,
    generate_clarification,
    finalize_log,
    analyze_input_streaming,
    generate_clarification_streaming,
    finalize_log_streaming,
)
from app.agent.routing import route_by_confidence
from app.agent.constants import (
    ANALYZE_INPUT,
    GENERATE_CLARIFICATION,
    FINALIZE_LOG,
    CONFIDENCE_THRESHOLD,
)
from app.schemas.sse import SSEEvent


def get_agent_graph():
    """
    Initialize and compile the agent graph with conditional routing.
    
    Graph Structure:
        START -> analyze_input -> [conditional edge]
            if confidence >= 0.85 or max_attempts: -> finalize_log -> END
            else: -> generate_clarification -> finalize_log -> END
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node(ANALYZE_INPUT, analyze_input)
    workflow.add_node(GENERATE_CLARIFICATION, generate_clarification)
    workflow.add_node(FINALIZE_LOG, finalize_log)

    # Entry point
    workflow.add_edge(START, ANALYZE_INPUT)

    # Conditional routing based on confidence
    workflow.add_conditional_edges(
        ANALYZE_INPUT,
        route_by_confidence,
        {
            GENERATE_CLARIFICATION: GENERATE_CLARIFICATION,
            FINALIZE_LOG: FINALIZE_LOG,
        },
    )

    # Clarification leads to finalize
    workflow.add_edge(GENERATE_CLARIFICATION, FINALIZE_LOG)
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
    - Low confidence (< 0.85): analyze -> clarification -> finalize

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
    overall_confidence = state.get("overall_confidence", 0.0)
    clarification_count = state.get("clarification_count", 0)

    # Route conditionally: skip clarification if high confidence or max attempts
    if overall_confidence < CONFIDENCE_THRESHOLD and clarification_count < 2:
        # Low confidence - run clarification
        async for item in generate_clarification_streaming(state):
            if isinstance(item, SSEEvent):
                yield item
            else:
                state.update(item)

    # Always run finalize
    async for item in finalize_log_streaming(state):
        if isinstance(item, SSEEvent):
            yield item
        else:
            state.update(item)

    # Final state is available in state dict
    yield state
