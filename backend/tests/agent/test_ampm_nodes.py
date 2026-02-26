"""Tests for AMPM node implementations."""

from unittest.mock import AsyncMock, patch

import pytest

from app.agent.ampm_nodes import (
    _is_non_answer,
    detail_cycle,
    detail_cycle_streaming,
    final_probe,
    final_probe_streaming,
)
from app.schemas.sse import SSEEvent
from app.services.llm_service import ClarificationQuestion

# --- Helper fixtures ---


def _make_state(
    overall_confidence=0.5,
    clarification_count=0,
    items=None,
    ampm_data=None,
    complexity_score=0.0,
    complexity_breakdown=None,
    language="en",
    log_id=None,
    clinical_threshold=15.0,
):
    """Create a minimal AgentState dict for testing."""
    if items is None:
        items = [
            {"name": "Mystery Dish", "quantity": "1 plate", "calories": 400, "confidence": 0.4},
        ]
    return {
        "messages": [],
        "image_url": None,
        "audio_url": None,
        "nutritional_data": {"items": items},
        "log_id": log_id,
        "overall_confidence": overall_confidence,
        "clarification_count": clarification_count,
        "needs_clarification": False,
        "needs_review": False,
        "user_token": None,
        "ampm_data": ampm_data,
        "current_pass": None,
        "complexity_score": complexity_score,
        "complexity_breakdown": complexity_breakdown,
        "start_time": None,
        "agent_turn_count": 0,
        "language": language,
        "system_prompt_override": None,
        "provider": None,
        "model": None,
        "is_food": True,
        "non_food_reason": None,
        "clinical_threshold": clinical_threshold,
    }


# --- Non-answer detection ---


class TestNonAnswerDetection:
    """Tests for non-answer phrase detection."""

    def test_english_non_answers(self):
        assert _is_non_answer("I don't know") is True
        assert _is_non_answer("not sure") is True
        assert _is_non_answer("no idea") is True

    def test_dutch_non_answers(self):
        assert _is_non_answer("weet ik niet") is True
        assert _is_non_answer("geen idee") is True

    def test_normal_answers_not_detected(self):
        assert _is_non_answer("It was grilled chicken") is False
        assert _is_non_answer("About 200 grams") is False

    def test_case_insensitive(self):
        assert _is_non_answer("I Don't Know") is True
        assert _is_non_answer("NOT SURE") is True


# --- detail_cycle (non-streaming) ---


class TestDetailCycle:
    """Tests for the detail_cycle node."""

    @pytest.mark.asyncio
    async def test_budget_exhausted_returns_needs_review(self):
        """When max clarifications reached, should return needs_review=True."""
        state = _make_state(clarification_count=2)
        result = await detail_cycle(state)
        assert result["needs_review"] is True
        assert result["needs_clarification"] is False

    @pytest.mark.asyncio
    async def test_no_low_confidence_items_returns_no_clarification(self):
        """When all items are high confidence, no clarification needed."""
        state = _make_state(items=[{"name": "Apple", "quantity": "1", "calories": 80, "confidence": 0.95}])
        result = await detail_cycle(state)
        assert result["needs_clarification"] is False

    @pytest.mark.asyncio
    async def test_generates_question_for_low_confidence(self):
        """Should generate a clarification question when low-confidence items exist."""
        mock_question = ClarificationQuestion(
            question="Was the dish fried or grilled?", options=["Fried", "Grilled"]
        )
        state = _make_state()

        with patch(
            "app.agent.ampm_nodes.llm_service.generate_clarification_question",
            new_callable=AsyncMock,
            return_value=mock_question,
        ):
            result = await detail_cycle(state)

        assert result["needs_clarification"] is True
        assert result["clarification_count"] == 1
        assert result["ampm_data"]["questions_asked"] == ["Was the dish fried or grilled?"]
        assert result["ampm_data"]["pass_count"] == 1

    @pytest.mark.asyncio
    async def test_skips_already_asked_items(self):
        """Should not re-ask about items from previous questions (non-answer handling)."""
        state = _make_state(
            ampm_data={
                "low_confidence_items": ["Mystery Dish"],
                "questions_asked": ["About your Mystery Dish..."],
                "responses": ["I don't know"],
                "pass_count": 1,
            },
            clarification_count=1,
        )
        result = await detail_cycle(state)
        assert result["needs_clarification"] is False

    @pytest.mark.asyncio
    async def test_llm_failure_returns_needs_review(self):
        """LLM failure should set needs_review=True and exit gracefully."""
        state = _make_state()

        with patch(
            "app.agent.ampm_nodes.llm_service.generate_clarification_question",
            new_callable=AsyncMock,
            side_effect=Exception("LLM timeout"),
        ):
            result = await detail_cycle(state)

        assert result["needs_review"] is True
        assert result["needs_clarification"] is False

    @pytest.mark.asyncio
    async def test_passes_dominant_factor_from_state(self):
        """Should pass dominant_factor from state to LLM service."""
        from app.schemas.analysis import AmbiguityLevels, ComplexityBreakdown

        complexity_breakdown = ComplexityBreakdown(
            score=0.8,
            dominant_factor="prep",
            levels=AmbiguityLevels(hidden_ingredients=0, invisible_prep=3, portion_ambiguity=0),
            weights={},
            semantic_penalty=0.0,
        )
        state = _make_state()
        state["complexity_breakdown"] = complexity_breakdown

        mock_question = ClarificationQuestion(question="How was it prepared?", options=["Fried", "Grilled"])

        with patch(
            "app.agent.ampm_nodes.llm_service.generate_clarification_question",
            new_callable=AsyncMock,
            return_value=mock_question,
        ) as mock_generate:
            await detail_cycle(state)

            # Verify dominant_factor was passed
            call_kwargs = mock_generate.call_args.kwargs
            assert call_kwargs["dominant_factor"] == "prep"


# --- final_probe (non-streaming) ---


class TestFinalProbe:
    """Tests for the final_probe node."""

    @pytest.mark.asyncio
    async def test_triggers_when_complex_and_inconclusive(self):
        """Should trigger when complexity_score > threshold and items still low confidence."""
        state = _make_state(complexity_score=16.0)
        result = await final_probe(state)
        assert result["needs_clarification"] is True

    @pytest.mark.asyncio
    async def test_skips_when_low_complexity(self):
        """Should skip when complexity_score <= threshold."""
        state = _make_state(complexity_score=14.0)
        result = await final_probe(state)
        assert result["needs_clarification"] is False

    @pytest.mark.asyncio
    async def test_skips_when_all_items_resolved(self):
        """Should skip when all items are above threshold (not inconclusive)."""
        state = _make_state(
            complexity_score=14.0,
            clinical_threshold=15.0,
            items=[{"name": "Apple", "quantity": "1", "calories": 80, "confidence": 0.95}],
        )
        result = await final_probe(state)
        assert result["needs_clarification"] is False


# --- detail_cycle_streaming ---


class TestDetailCycleStreaming:
    """Tests for the streaming variant of detail_cycle."""

    @pytest.mark.asyncio
    async def test_emits_thought_event(self):
        """Should emit a thought event at the start."""
        mock_question = ClarificationQuestion(question="How was it prepared?", options=["Fried", "Baked"])
        state = _make_state()

        events = []
        with patch(
            "app.agent.ampm_nodes.llm_service.generate_clarification_question",
            new_callable=AsyncMock,
            return_value=mock_question,
        ):
            async for item in detail_cycle_streaming(state):
                events.append(item)

        sse_events = [e for e in events if isinstance(e, SSEEvent)]
        assert len(sse_events) >= 1
        assert sse_events[0].type == "agent.thought"

    @pytest.mark.asyncio
    async def test_budget_exhausted_emits_state_update_only(self):
        """When budget exhausted, should yield state update without LLM call."""
        state = _make_state(clarification_count=2)

        events = []
        async for item in detail_cycle_streaming(state):
            events.append(item)

        # Should have thought event + state dict
        state_updates = [e for e in events if isinstance(e, dict)]
        assert any(su.get("needs_review") is True for su in state_updates)

    @pytest.mark.asyncio
    async def test_llm_error_emits_error_event(self):
        """LLM failure should emit an error SSE event."""
        state = _make_state()

        events = []
        with patch(
            "app.agent.ampm_nodes.llm_service.generate_clarification_question",
            new_callable=AsyncMock,
            side_effect=Exception("LLM error"),
        ):
            async for item in detail_cycle_streaming(state):
                events.append(item)

        sse_events = [e for e in events if isinstance(e, SSEEvent)]
        error_events = [e for e in sse_events if e.type == "agent.error"]
        assert len(error_events) == 1

    @pytest.mark.asyncio
    async def test_passes_dominant_factor_from_state_streaming(self):
        """Should pass dominant_factor from state to LLM service (streaming variant)."""
        from uuid import uuid4

        from app.schemas.analysis import AmbiguityLevels, ComplexityBreakdown

        complexity_breakdown = ComplexityBreakdown(
            score=0.8,
            dominant_factor="volume",
            levels=AmbiguityLevels(hidden_ingredients=0, invisible_prep=0, portion_ambiguity=3),
            weights={},
            semantic_penalty=0.0,
        )
        state = _make_state(log_id=uuid4(), complexity_breakdown=complexity_breakdown)

        mock_question = ClarificationQuestion(question="How much did you have?", options=["A cup", "A bowl"])

        with patch(
            "app.agent.ampm_nodes.llm_service.generate_clarification_question",
            new_callable=AsyncMock,
            return_value=mock_question,
        ) as mock_generate:
            events = []
            async for item in detail_cycle_streaming(state):
                events.append(item)

            call_kwargs = mock_generate.call_args.kwargs
            assert call_kwargs["dominant_factor"] == "volume"


# --- final_probe_streaming ---


class TestFinalProbeStreaming:
    """Tests for the streaming variant of final_probe."""

    @pytest.mark.asyncio
    async def test_emits_thought_and_clarification_when_triggered(self):
        """Should emit thought + clarification when conditions met."""
        from uuid import uuid4

        log_id = uuid4()
        state = _make_state(complexity_score=16.0, log_id=log_id)

        events = []
        async for item in final_probe_streaming(state):
            events.append(item)

        sse_events = [e for e in events if isinstance(e, SSEEvent)]
        assert any(e.type == "agent.thought" for e in sse_events)
        assert any(e.type == "agent.clarification" for e in sse_events)

    @pytest.mark.asyncio
    async def test_silent_when_not_triggered(self):
        """Should yield only state update when conditions not met."""
        state = _make_state(complexity_score=14.0)

        events = []
        async for item in final_probe_streaming(state):
            events.append(item)

        sse_events = [e for e in events if isinstance(e, SSEEvent)]
        assert len(sse_events) == 0
        state_updates = [e for e in events if isinstance(e, dict)]
        assert any(su.get("needs_clarification") is False for su in state_updates)
