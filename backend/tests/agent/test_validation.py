from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.agent.nodes import analyze_input_streaming
from app.schemas.analysis import AnalysisResult, FoodItem
from app.schemas.sse import SSEEvent


class TestInvalidValidation:
    """Tests for validation logic in nodes."""

    @pytest.mark.asyncio
    async def test_analyze_input_marks_invalid(self):
        """Should mark log as invalid when is_food is False."""
        log_id = uuid4()
        state = {
            "image_url": "http://example.com/shoe.jpg",
            "log_id": log_id,
            "agent_turn_count": 0,
        }

        # Mock LLM result with is_food=False
        analysis_result = AnalysisResult(
            title="Shoe",
            items=[],
            synthesis_comment="This is a shoe.",
            is_food=False,
            non_food_reason="It is a shoe, not food.",
        )

        mock_log = MagicMock()
        mock_log.status = "processing"
        mock_log.description = "Original description"

        with (
            patch(
                "app.agent.nodes.llm_service.analyze_multimodal_streaming", new_callable=AsyncMock
            ) as mock_analyze,
            patch("app.agent.nodes.database.async_session_maker") as mock_session_maker,
            patch("app.agent.nodes.llm_service._get_image_content", new_callable=AsyncMock),
        ):
            mock_analyze.return_value = analysis_result

            # Setup mock session
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_log
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock()

            events = []
            async for item in analyze_input_streaming(state):
                events.append(item)

            assert mock_log.status == "invalid"
            assert "[Invalid]: It is a shoe, not food." in mock_log.description

            response_events = [e for e in events if isinstance(e, SSEEvent) and e.type == "agent.response"]
            assert len(response_events) == 1
            assert response_events[0].payload.status == "invalid"

    @pytest.mark.asyncio
    async def test_analyze_input_valid_food(self):
        """Should NOT mark log as invalid when is_food is True (F4 coverage)."""
        log_id = uuid4()
        state = {
            "image_url": "http://example.com/salad.jpg",
            "log_id": log_id,
            "agent_turn_count": 0,
        }

        # Mock LLM result with is_food=True
        analysis_result = AnalysisResult(
            title="Salad",
            items=[FoodItem(name="Lettuce", quantity="1 cup", calories=10, confidence=0.9)],
            synthesis_comment="Looks like a healthy salad.",
            is_food=True,
            non_food_reason=None,
        )

        mock_log = MagicMock()
        mock_log.status = "processing"
        mock_log.description = "Original description"

        with (
            patch(
                "app.agent.nodes.llm_service.analyze_multimodal_streaming", new_callable=AsyncMock
            ) as mock_analyze,
            patch("app.agent.nodes.database.async_session_maker") as mock_session_maker,
            patch("app.agent.nodes.llm_service._get_image_content", new_callable=AsyncMock),
        ):
            mock_analyze.return_value = analysis_result

            # Setup mock session
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_log
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock()

            events = []
            async for item in analyze_input_streaming(state):
                events.append(item)

            # Assertions
            # Status should NOT be invalid.
            # In the real code, it sets it to 'created' later or leaves it as is until later steps.
            # analyze_input_streaming usually returns the generator and updates the log.
            # Let's verify we DID NOT set it to invalid.
            assert mock_log.status != "invalid"
            # It might be set to 'logged' or remains 'processing' depending on exact flow,
            # here we mainly care about valid inputs NOT triggering the invalid logic.
