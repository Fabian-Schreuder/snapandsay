"""Tests for the AMPM subgraph definition."""

import pytest
from langgraph.graph.state import CompiledStateGraph

from app.agent.ampm_graph import get_ampm_graph
from app.agent.constants import DETAIL_CYCLE, FINAL_PROBE


@pytest.mark.asyncio
async def test_get_ampm_graph_compiles():
    """Test that the AMPM subgraph compiles successfully."""
    graph = get_ampm_graph()
    assert isinstance(graph, CompiledStateGraph)


@pytest.mark.asyncio
async def test_ampm_graph_has_expected_nodes():
    """Test that the AMPM subgraph has detail_cycle and final_probe nodes."""
    graph = get_ampm_graph()
    assert DETAIL_CYCLE in graph.nodes
    assert FINAL_PROBE in graph.nodes
