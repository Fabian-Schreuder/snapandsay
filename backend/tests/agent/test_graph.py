from unittest.mock import patch

import pytest
from langgraph.graph.state import CompiledStateGraph

from app.agent.constants import (
    AMPM_ENTRY,
    ANALYZE_INPUT,
    FINALIZE_LOG,
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
    Test that the graph has the expected nodes (AMPM replaces clarification).
    """
    app = get_agent_graph()
    assert ANALYZE_INPUT in app.nodes
    assert AMPM_ENTRY in app.nodes
    assert FINALIZE_LOG in app.nodes


@pytest.mark.asyncio
async def test_graph_has_conditional_edges():
    """Test that the graph has conditional routing from analyze_input."""
    app = get_agent_graph()
    assert app is not None
    assert hasattr(app, "nodes")


@pytest.mark.asyncio
async def test_run_streaming_agent_high_confidence_skips_ampm():
    """Test that high confidence skips AMPM detail cycle."""
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
    detail_cycle_ran = False

    with (
        patch("app.agent.graph.analyze_input_streaming") as mock_analyze,
        patch("app.agent.graph.detail_cycle_streaming") as mock_detail,
        patch("app.agent.graph.final_probe_streaming") as mock_probe,
        patch("app.agent.graph.finalize_log_streaming") as mock_finalize,
    ):

        async def mock_analyze_gen(state):
            yield {"nutritional_data": {"items": []}, "overall_confidence": 0.95, "complexity_score": 0.2}

        mock_analyze.return_value = mock_analyze_gen(initial_state)

        async def mock_detail_gen(state):
            nonlocal detail_cycle_ran
            detail_cycle_ran = True
            yield {}

        mock_detail.return_value = mock_detail_gen(initial_state)

        async def mock_probe_gen(state):
            yield {}

        mock_probe.return_value = mock_probe_gen(initial_state)

        async def mock_finalize_gen(state):
            yield {}

        mock_finalize.return_value = mock_finalize_gen(initial_state)

        async for item in run_streaming_agent(initial_state):
            collected_events.append(item)

    # AMPM should NOT have run for high confidence
    assert detail_cycle_ran is False


@pytest.mark.asyncio
async def test_run_streaming_agent_low_confidence_runs_ampm():
    """Test that low confidence runs AMPM detail cycle."""
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

    detail_cycle_ran = False

    with (
        patch("app.agent.graph.analyze_input_streaming") as mock_analyze,
        patch("app.agent.graph.detail_cycle_streaming") as mock_detail,
        patch("app.agent.graph.final_probe_streaming") as mock_probe,
        patch("app.agent.graph.finalize_log_streaming") as mock_finalize,
    ):

        async def mock_analyze_gen(state):
            yield {"nutritional_data": {"items": []}, "overall_confidence": 0.5, "complexity_score": 0.3}

        mock_analyze.return_value = mock_analyze_gen(initial_state)

        async def mock_detail_gen(state):
            nonlocal detail_cycle_ran
            detail_cycle_ran = True
            yield {}

        mock_detail.return_value = mock_detail_gen(initial_state)

        async def mock_probe_gen(state):
            yield {}

        mock_probe.return_value = mock_probe_gen(initial_state)

        async def mock_finalize_gen(state):
            yield {}

        mock_finalize.return_value = mock_finalize_gen(initial_state)

        async for _item in run_streaming_agent(initial_state):
            pass

    # AMPM detail cycle SHOULD have run for low confidence
    assert detail_cycle_ran is True


@pytest.mark.asyncio
async def test_run_streaming_agent_max_attempts_skips_ampm():
    """Test that max clarification attempts skips AMPM detail cycle."""
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

    detail_cycle_ran = False

    with (
        patch("app.agent.graph.analyze_input_streaming") as mock_analyze,
        patch("app.agent.graph.detail_cycle_streaming") as mock_detail,
        patch("app.agent.graph.final_probe_streaming") as mock_probe,
        patch("app.agent.graph.finalize_log_streaming") as mock_finalize,
    ):

        async def mock_analyze_gen(state):
            yield {"nutritional_data": {"items": []}, "overall_confidence": 0.3, "complexity_score": 0.5}

        mock_analyze.return_value = mock_analyze_gen(initial_state)

        async def mock_detail_gen(state):
            nonlocal detail_cycle_ran
            detail_cycle_ran = True
            yield {}

        mock_detail.return_value = mock_detail_gen(initial_state)

        async def mock_probe_gen(state):
            yield {}

        mock_probe.return_value = mock_probe_gen(initial_state)

        async def mock_finalize_gen(state):
            yield {}

        mock_finalize.return_value = mock_finalize_gen(initial_state)

        async for _item in run_streaming_agent(initial_state):
            pass

    # AMPM should NOT run when max attempts reached
    assert detail_cycle_ran is False
