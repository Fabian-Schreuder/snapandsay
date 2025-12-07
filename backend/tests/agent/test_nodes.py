import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agent.nodes import analyze_input
from app.agent.state import AgentState
from app.schemas.analysis import AnalysisResult, FoodItem

@pytest.mark.asyncio
async def test_analyze_input_with_image_and_transcript():
    state: AgentState = {
        "messages": [],
        "image_url": "http://example.com/image.jpg",
        "audio_url": None,
        "nutritional_data": None
    }
    transcript = "Banana"
    analysis_result = AnalysisResult(items=[FoodItem(name="Banana", quantity="1", confidence=0.9)], synthesis_comment="OK")
    
    with patch("app.agent.nodes.llm_service.analyze_multimodal", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = analysis_result
        
        # Test case where transcript is passed directly if we modify the signature or state handling,
        # but here we might need to mock voice service if audio_url was present.
        # Wait, the node says "Call voice_service.transcribe if audio exists".
        # Let's simple test LLM call first.
        
        result = await analyze_input(state)
        
        # In current implementation plan, nodes.py calls llm_service.analyze_multimodal
        # But nodes.py logic: Check state["messages"] or state["image_url"].
        # If audio_url, transcribe.
        
        mock_analyze.assert_called_once_with(image_url="http://example.com/image.jpg", transcript=None, context=None)
        assert result["nutritional_data"] == analysis_result.model_dump()

@pytest.mark.asyncio
async def test_analyze_input_with_audio():
    state: AgentState = {
        "messages": [],
        "image_url": None,
        "audio_url": "audio.mp3",
        "nutritional_data": None
    }
    
    transcript = "I ate a burger"
    analysis_result = AnalysisResult(items=[FoodItem(name="Burger", quantity="1", confidence=0.9)], synthesis_comment="OK")
    
    with patch("app.agent.nodes.voice_service.transcribe_audio", new_callable=AsyncMock) as mock_transcribe, \
         patch("app.agent.nodes.llm_service.analyze_multimodal", new_callable=AsyncMock) as mock_analyze:
        
        mock_transcribe.return_value = transcript
        mock_analyze.return_value = analysis_result
        
        result = await analyze_input(state)
        
        mock_transcribe.assert_called_once_with("audio.mp3")
        mock_analyze.assert_called_once_with(image_url=None, transcript=transcript, context=None)
        assert result["nutritional_data"] == analysis_result.model_dump()
