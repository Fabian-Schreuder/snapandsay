"""AMPM (Automated Multi-Pass Method) node implementations.

This module contains the Detail Cycle and Final Probe nodes for the AMPM
subgraph. Each node has both a non-streaming and streaming variant to
support both execution paths in the agent graph.

Note: AMPM streaming logic is mirrored in run_streaming_agent() — keep in sync.
"""

import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from sqlalchemy import select

from app.agent.constants import (
    CONFIDENCE_THRESHOLD,
    EVENT_CLARIFICATION,
    EVENT_ERROR,
    EVENT_THOUGHT,
    MAX_CLARIFICATIONS,
    STEP_DETAIL_CYCLE,
    STEP_FINAL_PROBE,
    get_message,
)
from app.agent.state import AgentState
from app.database import async_session_maker
from app.models.log import DietaryLog
from app.schemas.analysis import FoodItem
from app.schemas.sse import (
    AgentClarification,
    AgentError,
    AgentThought,
    SSEEvent,
)
from app.services import llm_service

logger = logging.getLogger(__name__)

# Phrases indicating user doesn't know the answer (EN + NL)
_NON_ANSWER_PHRASES = {
    "i don't know",
    "i dont know",
    "not sure",
    "no idea",
    "don't remember",
    "dont remember",
    "weet ik niet",
    "geen idee",
    "weet niet",
    "niet zeker",
}


def _is_non_answer(response: str) -> bool:
    """Check if the user's response is a non-answer (e.g. 'I don't know')."""
    return response.strip().lower() in _NON_ANSWER_PHRASES


def _get_low_confidence_items(state: AgentState) -> list[FoodItem]:
    """Extract low-confidence FoodItems from the current nutritional data."""
    nutritional_data = state.get("nutritional_data", {}) or {}
    items = nutritional_data.get("items", [])
    force_clarify = state.get("force_clarify", False)

    if force_clarify:
        return [FoodItem(**item) for item in items]

    return [FoodItem(**item) for item in items if item.get("confidence", 1.0) < CONFIDENCE_THRESHOLD]


def _already_asked(item_name: str, state: AgentState) -> bool:
    """Check if we've already asked about this item (to avoid re-asking after non-answer)."""
    ampm_data = state.get("ampm_data")
    if not ampm_data:
        return False
    return any(item_name.lower() in q.lower() for q in ampm_data.get("questions_asked", []))


def _is_detail_cycle_inconclusive(state: AgentState) -> bool:
    """Check if the detail cycle was inconclusive (items still below threshold)."""
    low_items = _get_low_confidence_items(state)
    return len(low_items) > 0


# --- Non-Streaming Variants (for compiled graph) ---


async def detail_cycle(state: AgentState) -> dict:
    """
    AMPM Detail Cycle: identify low-confidence items and generate
    a targeted clarification question, prioritized by nutritional variance impact.
    """
    clarification_count = state.get("clarification_count", 0)

    # Guard: budget exhausted
    if clarification_count >= MAX_CLARIFICATIONS:
        return {"needs_review": True, "needs_clarification": False}

    low_items = _get_low_confidence_items(state)

    # Filter out items we've already asked about (non-answer handling)
    askable_items = [item for item in low_items if not _already_asked(item.name, state)]

    if not askable_items:
        return {"needs_clarification": False}

    try:
        question = await llm_service.generate_clarification_question(
            askable_items,
            language=state.get("language", "nl") or "nl",
            provider=state.get("provider"),
            model=state.get("model"),
        )

        # Update log status to clarification in database
        log_id = state.get("log_id")
        if log_id:
            async with async_session_maker() as session:
                result = await session.execute(select(DietaryLog).where(DietaryLog.id == log_id))
                log_entry = result.scalar_one_or_none()
                if log_entry:
                    log_entry.status = "clarification"
                    await session.commit()
                    logger.info(f"AMPM: Updated log {log_id} status to 'clarification'")

        # Update AMPM tracking data
        ampm_data = state.get("ampm_data") or {
            "low_confidence_items": [],
            "questions_asked": [],
            "responses": [],
            "pass_count": 0,
        }
        ampm_data = dict(ampm_data)  # Make mutable copy
        ampm_data["low_confidence_items"] = [item.name for item in low_items]
        ampm_data["questions_asked"].append(question.question)
        ampm_data["pass_count"] += 1

        return {
            "needs_clarification": True,
            "clarification_count": clarification_count + 1,
            "ampm_data": ampm_data,
            "agent_turn_count": state.get("agent_turn_count", 0) + 1,
        }
    except Exception as e:
        logger.error(f"AMPM detail_cycle LLM call failed: {e}")
        return {"needs_review": True, "needs_clarification": False}


async def detail_cycle_streaming(
    state: AgentState,
) -> AsyncGenerator[SSEEvent | dict, None]:
    """
    Streaming variant of the AMPM Detail Cycle.

    Emits SSE events during processing and yields a state update dict at the end.
    """
    language = state.get("language", "nl") or "nl"
    clarification_count = state.get("clarification_count", 0)
    log_id = state.get("log_id")

    # Emit thought event
    yield SSEEvent(
        type=EVENT_THOUGHT,
        payload=AgentThought(
            step=STEP_DETAIL_CYCLE,
            message=get_message("detail_cycle_start", language),
            timestamp=datetime.now(UTC),
        ),
    )

    # Guard: budget exhausted
    if clarification_count >= MAX_CLARIFICATIONS:
        yield {"needs_review": True, "needs_clarification": False}
        return

    low_items = _get_low_confidence_items(state)

    # Filter out items we've already asked about (non-answer handling)
    askable_items = [item for item in low_items if not _already_asked(item.name, state)]

    if not askable_items:
        yield {"needs_clarification": False}
        return

    try:
        question = await llm_service.generate_clarification_question(
            askable_items,
            language=language,
            provider=state.get("provider"),
            model=state.get("model"),
        )

        # Update log status to clarification in database
        if log_id:
            async with async_session_maker() as session:
                result = await session.execute(select(DietaryLog).where(DietaryLog.id == log_id))
                log_entry = result.scalar_one_or_none()
                if log_entry:
                    log_entry.status = "clarification"
                    await session.commit()
                    logger.info(f"AMPM Streaming: Updated log {log_id} status to 'clarification'")

        # Update AMPM tracking data
        ampm_data = state.get("ampm_data") or {
            "low_confidence_items": [],
            "questions_asked": [],
            "responses": [],
            "pass_count": 0,
        }
        ampm_data = dict(ampm_data)  # Make mutable copy
        ampm_data["low_confidence_items"] = [item.name for item in low_items]
        ampm_data["questions_asked"].append(question.question)
        ampm_data["pass_count"] += 1

        # Emit clarification event (reuses existing SSE schema)
        if log_id:
            context = {
                "items": [{"name": item.name, "confidence": item.confidence} for item in askable_items]
            }
            yield SSEEvent(
                type=EVENT_CLARIFICATION,
                payload=AgentClarification(
                    question=question.question,
                    options=question.options,
                    context=context,
                    log_id=log_id,
                ),
            )

        yield {
            "needs_clarification": True,
            "clarification_count": clarification_count + 1,
            "ampm_data": ampm_data,
            "agent_turn_count": state.get("agent_turn_count", 0) + 1,
        }
    except Exception as e:
        logger.error(f"AMPM detail_cycle_streaming LLM call failed: {e}")
        yield SSEEvent(
            type=EVENT_ERROR,
            payload=AgentError(
                code="AMPM_DETAIL_CYCLE_ERROR",
                message=get_message("error_internal", language),
            ),
        )
        yield {"needs_review": True, "needs_clarification": False}


async def final_probe(state: AgentState) -> dict:
    """
    AMPM Final Probe: conditionally ask "Did you have anything else with that?"

    Only triggers if:
      - complexity_score > 0.7 (meal is inherently complex)
      - Detail Cycle was inconclusive (items still below threshold)
    """
    complexity_score = state.get("complexity_score", 0.0)
    inconclusive = _is_detail_cycle_inconclusive(state)

    if complexity_score > 0.7 and inconclusive:
        # The final probe question is handled via streaming/clarification;
        # in the compiled graph path we just mark state.
        return {"needs_clarification": True}

    return {"needs_clarification": False}


async def final_probe_streaming(
    state: AgentState,
) -> AsyncGenerator[SSEEvent | dict, None]:
    """
    Streaming variant of the AMPM Final Probe.

    Conditionally emits the "Did you have anything else with that?" question.
    """
    language = state.get("language", "nl") or "nl"
    complexity_score = state.get("complexity_score", 0.0)
    inconclusive = _is_detail_cycle_inconclusive(state)
    log_id = state.get("log_id")

    if complexity_score > 0.7 and inconclusive:
        try:
            yield SSEEvent(
                type=EVENT_THOUGHT,
                payload=AgentThought(
                    step=STEP_FINAL_PROBE,
                    message=get_message("final_probe", language),
                    timestamp=datetime.now(UTC),
                ),
            )

            if log_id:
                # Update log status to clarification in database
                async with async_session_maker() as session:
                    result = await session.execute(select(DietaryLog).where(DietaryLog.id == log_id))
                    log_entry = result.scalar_one_or_none()
                    if log_entry:
                        log_entry.status = "clarification"
                        await session.commit()
                        logger.info(f"AMPM Final Probe: Updated log {log_id} status to 'clarification'")

                yield SSEEvent(
                    type=EVENT_CLARIFICATION,
                    payload=AgentClarification(
                        question=get_message("final_probe", language),
                        options=[],
                        context={"type": "final_probe"},
                        log_id=log_id,
                    ),
                )

            yield {"needs_clarification": True}
        except Exception as e:
            logger.error(f"AMPM final_probe_streaming failed: {e}")
            yield SSEEvent(
                type=EVENT_ERROR,
                payload=AgentError(
                    code="AMPM_FINAL_PROBE_ERROR",
                    message=get_message("error_internal", language),
                ),
            )
            yield {"needs_review": True, "needs_clarification": False}
    else:
        # No probe needed — pass through silently
        yield {"needs_clarification": False}
