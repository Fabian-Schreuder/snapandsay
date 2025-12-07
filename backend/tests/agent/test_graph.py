import pytest
from app.agent.graph import get_agent_graph
from langgraph.graph.state import CompiledStateGraph

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
    assert "analyze_input" in app.nodes
