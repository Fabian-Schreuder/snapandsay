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
from app.agent.constants import ANALYZE_INPUT, GENERATE_CLARIFICATION, FINALIZE_LOG
from app.schemas.sse import SSEEvent


def get_agent_graph():
    """
    Initialize and compile the agent graph.
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node(ANALYZE_INPUT, analyze_input)
    workflow.add_node(GENERATE_CLARIFICATION, generate_clarification)
    workflow.add_node(FINALIZE_LOG, finalize_log)

    # Currently only formatting the start of the flow involving analysis
    workflow.add_edge(START, ANALYZE_INPUT)
    
    # Placeholder flow: Connect all nodes to ensure reachability
    workflow.add_edge(ANALYZE_INPUT, GENERATE_CLARIFICATION)
    workflow.add_edge(GENERATE_CLARIFICATION, FINALIZE_LOG)
    workflow.add_edge(FINALIZE_LOG, END)

    # Compile the graph
    app = workflow.compile()
    return app


async def run_streaming_agent(
    initial_state: AgentState,
) -> AsyncGenerator[SSEEvent | dict, None]:
    """
    Run the agent graph with streaming SSE events.

    This function executes the agent nodes in sequence, yielding
    SSE events as each node processes, and returning the final state.

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

    # Run generate_clarification_streaming
    async for item in generate_clarification_streaming(state):
        if isinstance(item, SSEEvent):
            yield item
        else:
            state.update(item)

    # Run finalize_log_streaming
    async for item in finalize_log_streaming(state):
        if isinstance(item, SSEEvent):
            yield item
        else:
            state.update(item)

    # Final state is available in state dict
    yield state
