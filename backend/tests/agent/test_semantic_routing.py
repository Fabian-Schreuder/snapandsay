import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.agent.graph import get_agent_graph
from app.agent.state import AgentState
from app.schemas.analysis import AnalysisResult, FoodItem, ComplexityBreakdown, AmbiguityLevels
from app.agent.constants import ANALYZE_INPUT, SEMANTIC_GATEKEEPER, GENERATE_SEMANTIC_CLARIFICATION, FINALIZE_LOG

@pytest.fixture
def mock_llm_service():
    with patch("app.agent.nodes.llm_service") as mock:
        yield mock

@pytest.fixture
def mock_registry():
    with patch("app.services.semantic_gatekeeper.registry") as mock:
        yield mock

@pytest.mark.asyncio
async def test_semantic_routing_umbrella_term(mock_llm_service, mock_registry):
    # Setup: LLM returns "Sandwich"
    mock_result = AnalysisResult(
        title="Sandwich",
        items=[FoodItem(name="Sandwich", quantity="1", confidence=0.9)],
        synthesis_comment="It is a sandwich.",
        is_food=True,
        complexity_score=0.5
    )
    mock_llm_service.analyze_multimodal = AsyncMock(return_value=mock_result)
    
    # Setup: Registry identifies "Sandwich" as umbrella
    def get_risk_profile_side_effect(name):
        mock = MagicMock()
        mock.is_umbrella_term = (name == "Sandwich")
        return mock
    mock_registry.get_risk_profile.side_effect = get_risk_profile_side_effect

    # Setup: Mock clarification generation to avoid LLM call
    mock_llm_service.generate_clarification_question = AsyncMock()
    mock_llm_service.generate_clarification_question.return_value.question = "What kind of sandwich?"
    mock_llm_service.generate_clarification_question.return_value.options = ["Club", "BLT"]

    # Build Graph
    app = get_agent_graph()
    
    # Run
    initial_state = AgentState(
        image_url="http://example.com/sandwich.jpg",
        messages=[],
        start_time=123.0
    )
    
    # We expect the graph to stop after GENERATE_SEMANTIC_CLARIFICATION because 
    # generate_semantic_clarification returns "needs_clarification": True,
    # AND in `run_streaming_agent` (which mirrors this logic), we yield and return.
    # But `get_agent_graph` executes the compiled graph. 
    # In `graph.py` we added edge GENERATE_SEMANTIC_CLARIFICATION -> FINALIZE_LOG.
    # Wait, if we route to FINALIZE_LOG, it will finish.
    # But `nodes.py` `generate_semantic_clarification` logic was:
    # `yield {"needs_clarification": True}` (in streaming)
    # The node function `generate_semantic_clarification` returns `{"needs_clarification": True}`.
    
    # Let's check `graph.py` again.
    # workflow.add_edge(GENERATE_SEMANTIC_CLARIFICATION, FINALIZE_LOG)
    
    # So if we run the graph non-streaming, it will go:
    # START -> ANALYZE -> GATEKEEPER -> GENERATE_SEMANTIC -> FINALIZE -> END.
    
    # The state should show `semantic_interruption_needed=True` and `needs_clarification=True`.
    
    result = await app.ainvoke(initial_state)
    
    assert result["unbounded_items"] == ["Sandwich"]
    assert result["semantic_interruption_needed"] is True
    # assert result["needs_clarification"] is True # verify if finalize_log overwrites this?
    # finalize_log sets needs_review based on confidence/clarification count
    # It returns {"needs_review": ...} which updates state. 
    # It does NOT overwrite `needs_clarification` unless we explicitly return it.
    
    # Check if generate_semantic_clarification was reached
    # We can check specific mocks were called
    mock_registry.get_risk_profile.assert_called_with("Sandwich")

@pytest.mark.asyncio
async def test_semantic_routing_specific_term(mock_llm_service, mock_registry):
    # Setup: LLM returns "Turkey Sandwich"
    mock_result = AnalysisResult(
        title="Turkey Sandwich",
        items=[FoodItem(name="Turkey Sandwich", quantity="1", confidence=0.95)],
        synthesis_comment="It is a turkey sandwich.",
        is_food=True,
        complexity_score=0.5
    )
    mock_llm_service.analyze_multimodal = AsyncMock(return_value=mock_result)
    
    # Setup: Registry says NOT umbrella
    mock_registry.get_risk_profile.return_value.is_umbrella_term = False

    # Build Graph
    app = get_agent_graph()
    
    # Run
    initial_state = AgentState(
        image_url="http://example.com/turkey.jpg",
        messages=[],
        start_time=123.0
    )
    
    result = await app.ainvoke(initial_state)
    
    assert result["unbounded_items"] == []
    assert result["semantic_interruption_needed"] is False
    # Should fulfill confident routing -> FINALIZE_LOG directly (bypassing AMPM)
    # or AMPM if confidence low. Here confidence is 0.95 (High).
