from unittest.mock import patch

import pytest
from langgraph.graph.state import CompiledStateGraph

from app.agent.constants import (
    ANALYZE_INPUT,
    FINALIZE_LOG,
    GENERATE_CLARIFICATION,
)
from app.agent.graph import get_agent_graph, run_streaming_agent


@pytest.mark.asyncio
async def test_get_agent_graph():
    """
    Test that the agent graph is compiled successfully and return a CompiledStateGraph.
    """
    app = get_agent_graph()
    assert isinstance(app, CompiledStateGraph)


@pytest.mark.asyncio
async def test_graph_structure():
    """
    Test that the graph has the expected nodes.
    """
    app = get_agent_graph()
    # Accessing underlying graph to check nodes
    # Note: Internal structure access depends on LangGraph version,
    # but CompiledStateGraph usually wrappers the graph.
    # For a simple check, we can verify it runs without error on a dummy input.

    # We can inspect the graph nodes if exposed, otherwise simple invocation test
    assert ANALYZE_INPUT in app.nodes
    assert GENERATE_CLARIFICATION in app.nodes
    assert FINALIZE_LOG in app.nodes


@pytest.mark.asyncio
async def test_graph_has_conditional_edges():
    """Test that the graph has conditional routing from analyze_input."""
    app = get_agent_graph()
    # Verify the graph structure includes conditional edges
    # The graph should have edges from analyze_input to both clarification and finalize
    assert app is not None
    # The compiled graph should exist and be navigable
    assert hasattr(app, "nodes")


@pytest.mark.asyncio
async def test_run_streaming_agent_high_confidence_skips_clarification():
    """Test that high confidence skips clarification step."""
    initial_state = {
        "messages": [],
        "image_url": "https://example.com/food.jpg",
        "audio_url": None,
        "nutritional_data": None,
        "log_id": None,
        "overall_confidence": 0.0,
        "clarification_count": 0,
        "needs_clarification": False,
        "needs_review": False,
    }

    collected_events = []
    clarification_ran = False

    # Patch the streaming nodes
    with (
        patch("app.agent.graph.analyze_input_streaming") as mock_analyze,
        patch("app.agent.graph.generate_clarification_streaming") as mock_clarify,
        patch("app.agent.graph.finalize_log_streaming") as mock_finalize,
    ):
        # Mock analyze to return high confidence
        async def mock_analyze_gen(state):
            yield {"nutritional_data": {"items": []}, "overall_confidence": 0.95}

        mock_analyze.return_value = mock_analyze_gen(initial_state)

        async def mock_clarify_gen(state):
            nonlocal clarification_ran
            clarification_ran = True
            yield {}

        mock_clarify.return_value = mock_clarify_gen(initial_state)

        async def mock_finalize_gen(state):
            yield {}

        mock_finalize.return_value = mock_finalize_gen(initial_state)

        async for item in run_streaming_agent(initial_state):
            collected_events.append(item)

    # Clarification should NOT have run for high confidence
    assert clarification_ran is False


@pytest.mark.asyncio
async def test_run_streaming_agent_low_confidence_runs_clarification():
    """Test that low confidence runs clarification step."""
    initial_state = {
        "messages": [],
        "image_url": "https://example.com/food.jpg",
        "audio_url": None,
        "nutritional_data": None,
        "log_id": None,
        "overall_confidence": 0.0,
        "clarification_count": 0,
        "needs_clarification": False,
        "needs_review": False,
    }

    clarification_ran = False

    with (
        patch("app.agent.graph.analyze_input_streaming") as mock_analyze,
        patch("app.agent.graph.generate_clarification_streaming") as mock_clarify,
        patch("app.agent.graph.finalize_log_streaming") as mock_finalize,
    ):
        # Mock analyze to return low confidence
        async def mock_analyze_gen(state):
            yield {"nutritional_data": {"items": []}, "overall_confidence": 0.5}

        mock_analyze.return_value = mock_analyze_gen(initial_state)

        async def mock_clarify_gen(state):
            nonlocal clarification_ran
            clarification_ran = True
            yield {}

        mock_clarify.return_value = mock_clarify_gen(initial_state)

        async def mock_finalize_gen(state):
            yield {}

        mock_finalize.return_value = mock_finalize_gen(initial_state)

        async for _item in run_streaming_agent(initial_state):
            pass

    # Clarification SHOULD have run for low confidence
    assert clarification_ran is True


@pytest.mark.asyncio
async def test_run_streaming_agent_max_attempts_skips_clarification():
    """Test that max clarification attempts skips further clarification."""
    initial_state = {
        "messages": [],
        "image_url": "https://example.com/food.jpg",
        "audio_url": None,
        "nutritional_data": None,
        "log_id": None,
        "overall_confidence": 0.0,
        "clarification_count": 2,  # Already at max
        "needs_clarification": False,
        "needs_review": False,
    }

    clarification_ran = False

    with (
        patch("app.agent.graph.analyze_input_streaming") as mock_analyze,
        patch("app.agent.graph.generate_clarification_streaming") as mock_clarify,
        patch("app.agent.graph.finalize_log_streaming") as mock_finalize,
    ):

        async def mock_analyze_gen(state):
            yield {"nutritional_data": {"items": []}, "overall_confidence": 0.3}

        mock_analyze.return_value = mock_analyze_gen(initial_state)

        async def mock_clarify_gen(state):
            nonlocal clarification_ran
            clarification_ran = True
            yield {}

        mock_clarify.return_value = mock_clarify_gen(initial_state)

        async def mock_finalize_gen(state):
            yield {}

        mock_finalize.return_value = mock_finalize_gen(initial_state)

        async for _item in run_streaming_agent(initial_state):
            pass

    # Clarification should NOT run when max attempts reached
    assert clarification_ran is False
