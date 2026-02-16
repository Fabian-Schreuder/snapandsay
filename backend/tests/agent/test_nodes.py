from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.agent.nodes import (
    analyze_input,
    finalize_log,
    finalize_log_streaming,
    generate_clarification,
    generate_clarification_streaming,
)
from app.agent.state import AgentState
from app.schemas.analysis import AnalysisResult, FoodItem
from app.schemas.sse import SSEEvent
from app.services.llm_service import ClarificationQuestion


@pytest.mark.asyncio
async def test_analyze_input_with_image_and_transcript():
    state: AgentState = {
        "messages": [],
        "image_url": "http://example.com/image.jpg",
        "audio_url": None,
        "nutritional_data": None,
    }
    analysis_result = AnalysisResult(
        title="Test Meal",
        items=[FoodItem(name="Banana", quantity="1", confidence=0.9)],
        synthesis_comment="OK",
    )

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

        mock_analyze.assert_called_once_with(
            image_url="http://example.com/image.jpg",
            transcript=None,
            context=None,
            user_token=None,
            system_prompt_override=None,
            provider=None,
            model=None,
        )
        assert result["nutritional_data"] == analysis_result.model_dump()


@pytest.mark.asyncio
async def test_analyze_input_with_audio():
    state: AgentState = {
        "messages": [],
        "image_url": None,
        "audio_url": "audio.mp3",
        "nutritional_data": None,
    }

    transcript = "I ate a burger"
    analysis_result = AnalysisResult(
        title="Burger Meal",
        items=[FoodItem(name="Burger", quantity="1", confidence=0.9)],
        synthesis_comment="OK",
    )

    with (
        patch("app.agent.nodes.voice_service.transcribe_audio", new_callable=AsyncMock) as mock_transcribe,
        patch("app.agent.nodes.llm_service.analyze_multimodal", new_callable=AsyncMock) as mock_analyze,
    ):
        mock_transcribe.return_value = transcript
        mock_analyze.return_value = analysis_result

        result = await analyze_input(state)

        mock_transcribe.assert_called_once_with("audio.mp3", token=None)
        mock_analyze.assert_called_once_with(
            image_url=None,
            transcript=transcript,
            context=None,
            user_token=None,
            system_prompt_override=None,
            provider=None,
            model=None,
        )
        assert result["nutritional_data"] == analysis_result.model_dump()


class TestGenerateClarification:
    """Tests for generate_clarification node."""

    @pytest.mark.asyncio
    async def test_generates_question_for_low_confidence_items(self):
        """Should generate clarification when items have low confidence."""
        state = {
            "nutritional_data": {
                "items": [{"name": "Salad", "quantity": "1 bowl", "confidence": 0.6, "calories": 150}]
            },
            "clarification_count": 0,
        }

        mock_question = ClarificationQuestion(
            question="What kind of dressing?", options=["Ranch", "Italian", "None"]
        )

        with patch(
            "app.agent.nodes.llm_service.generate_clarification_question", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = mock_question
            result = await generate_clarification(state)

            assert result["needs_clarification"] is True
            assert result["clarification_count"] == 1

    @pytest.mark.asyncio
    async def test_no_clarification_for_high_confidence(self):
        """Should not generate clarification when items have high confidence."""
        state = {
            "nutritional_data": {
                "items": [{"name": "Apple", "quantity": "1", "confidence": 0.95, "calories": 95}]
            },
            "clarification_count": 0,
        }

        result = await generate_clarification(state)
        assert result["needs_clarification"] is False

    @pytest.mark.asyncio
    async def test_empty_items_no_clarification(self):
        """Should not generate clarification when no items exist."""
        state = {
            "nutritional_data": {"items": []},
            "clarification_count": 0,
        }

        result = await generate_clarification(state)
        assert result["needs_clarification"] is False


class TestGenerateClarificationStreaming:
    """Tests for generate_clarification_streaming node."""

    @pytest.mark.asyncio
    async def test_emits_clarification_event_and_updates_db(self):
        """Should emit SSE event and update DB status to clarification."""
        log_id = uuid4()
        state = {
            "nutritional_data": {
                "items": [{"name": "Mystery dish", "quantity": "1 plate", "confidence": 0.5, "calories": 200}]
            },
            "clarification_count": 0,
            "log_id": log_id,
        }

        mock_question = ClarificationQuestion(
            question="What type of food is this?", options=["Pasta", "Rice", "Other"]
        )

        mock_log = MagicMock()
        mock_log.status = "processing"

        with (
            patch(
                "app.agent.nodes.llm_service.generate_clarification_question",
                new_callable=AsyncMock,
                return_value=mock_question,
            ),
            patch("app.agent.nodes.async_session_maker") as mock_session_maker,
        ):
            # Setup mock session context manager
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_log
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            mock_session.add = MagicMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock()

            events = []
            async for item in generate_clarification_streaming(state):
                events.append(item)

            # Should have emitted thought, clarification event, and state update
            assert len(events) >= 2

            # Check clarification event was emitted
            clarification_events = [
                e for e in events if isinstance(e, SSEEvent) and e.type == "agent.clarification"
            ]
            assert len(clarification_events) == 1
            assert clarification_events[0].payload.question == "What type of food is this?"

            # Check DB status was updated
            assert mock_log.status == "clarification"


class TestFinalizeLog:
    """Tests for finalize_log node."""

    @pytest.mark.asyncio
    async def test_sets_needs_review_when_low_confidence_max_attempts(self):
        """Should set needs_review when confidence low after max attempts."""
        state = {
            "overall_confidence": 0.5,
            "clarification_count": 2,
            "needs_review": False,
        }

        result = await finalize_log(state)
        assert result["needs_review"] is True

    @pytest.mark.asyncio
    async def test_no_review_for_high_confidence(self):
        """Should not set needs_review for high confidence."""
        state = {
            "overall_confidence": 0.9,
            "clarification_count": 0,
            "needs_review": False,
        }

        result = await finalize_log(state)
        assert result["needs_review"] is False


class TestFinalizeLogStreaming:
    """Tests for finalize_log_streaming node."""

    @pytest.mark.asyncio
    async def test_persists_to_db_with_logged_status(self):
        """Should persist log to DB with status='logged'."""
        log_id = uuid4()
        state = {
            "log_id": log_id,
            "nutritional_data": {
                "items": [{"name": "Apple", "quantity": "1", "confidence": 0.95, "calories": 95}],
                "synthesis_comment": "Healthy snack",
            },
            "overall_confidence": 0.95,
            "clarification_count": 0,
            "needs_review": False,
        }

        mock_log = MagicMock()
        mock_log.status = "processing"
        mock_log.description = None

        with patch("app.agent.nodes.async_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_log
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            mock_session.add = MagicMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock()

            events = []
            async for item in finalize_log_streaming(state):
                events.append(item)

            # Check DB was updated
            assert mock_log.status == "logged"
            assert mock_log.needs_review is False
            assert mock_log.calories == 95
            assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_flags_needs_review_after_max_attempts(self):
        """Should set needs_review flag after max clarification attempts."""
        log_id = uuid4()
        state = {
            "log_id": log_id,
            "nutritional_data": {"items": [], "synthesis_comment": ""},
            "overall_confidence": 0.4,
            "clarification_count": 2,
            "needs_review": False,
        }

        mock_log = MagicMock()
        mock_log.status = "processing"
        mock_log.description = None

        with patch("app.agent.nodes.async_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_log
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            mock_session.add = MagicMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock()

            events = []
            async for item in finalize_log_streaming(state):
                events.append(item)

            assert mock_log.needs_review is True

    @pytest.mark.asyncio
    async def test_emits_response_event(self):
        """Should emit agent.response SSE event."""
        log_id = uuid4()
        state = {
            "log_id": log_id,
            "nutritional_data": {"items": [], "synthesis_comment": ""},
            "overall_confidence": 0.9,
            "clarification_count": 0,
            "needs_review": False,
        }

        mock_log = MagicMock()
        mock_log.status = "processing"
        mock_log.description = None

        with patch("app.agent.nodes.async_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_log
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            mock_session.add = MagicMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock()

            events = []
            async for item in finalize_log_streaming(state):
                events.append(item)

            response_events = [e for e in events if isinstance(e, SSEEvent) and e.type == "agent.response"]
            assert len(response_events) == 1
            assert response_events[0].payload.status == "logged"
