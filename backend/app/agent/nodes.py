import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from sqlalchemy import select

from app import database
from app.agent.constants import (
    CONFIDENCE_THRESHOLD,
    EVENT_CLARIFICATION,
    EVENT_ERROR,
    EVENT_RESPONSE,
    EVENT_THOUGHT,
    STEP_ANALYZING,
    STEP_CLARIFYING,
    STEP_FINALIZING,
    STEP_SEMANTIC_CHECK,
    get_message,
)
from app.agent.state import AgentState
from app.models.log import DietaryLog
from app.schemas.analysis import AnalysisResult, FoodItem
from app.schemas.sse import (
    AgentClarification,
    AgentError,
    AgentResponse,
    AgentThought,
    SSEEvent,
)
from app.services import llm_service, semantic_gatekeeper, voice_service
from app.services.complexity_calculator import calculate_complexity
from app.services.food_class_registry import RiskProfile
from app.services.food_class_registry import registry as food_registry

logger = logging.getLogger(__name__)


def _enrich_with_complexity(result: AnalysisResult) -> None:
    """
    Enrich the AnalysisResult with deterministic complexity score.
    Refines the LLM-provided breakdown with calculated values.
    """
    if not result.complexity_breakdown or not result.complexity_breakdown.levels:
        logger.warning("No ambiguity levels found in analysis result, skipping deterministic scoring")
        return

    levels = result.complexity_breakdown.levels

    # Collect risk profiles from registry matches (title + items).
    # Use cached lookup key to avoid redundant substring search in get_risk_profile.
    profiles: list[RiskProfile] = []

    if result.title:
        class_key = food_registry.lookup(result.title)
        if class_key:
            profiles.append(food_registry.get_risk_profile(result.title))

    for item in result.items:
        class_key = food_registry.lookup(item.name)
        if class_key:
            profiles.append(food_registry.get_risk_profile(item.name))

    # Pick most conservative profile (highest semantic_penalty), else default
    if profiles:
        profiles.sort(key=lambda p: p.semantic_penalty, reverse=True)
        selected_profile = profiles[0]
    else:
        selected_profile = food_registry.get_risk_profile("")

    full_breakdown = calculate_complexity(levels, selected_profile)

    result.complexity_breakdown = full_breakdown
    result.complexity_score = full_breakdown.score
    if selected_profile.mandatory_clarification:
        result.mandatory_clarification = True
        logger.info("Mandatory clarification triggered by risk profile: %s", selected_profile.name)

    logger.info(
        "Calculated deterministic complexity: %s (Dominant: %s)",
        result.complexity_score,
        full_breakdown.dominant_factor,
    )


async def analyze_input(state: AgentState) -> dict:
    """
    Analyze the input (image or text) to determine the next step.
    fetches clarification context from DB if log_id exists.
    """
    image_url = state.get("image_url")
    audio_url = state.get("audio_url")
    log_id = state.get("log_id")
    user_token = state.get("user_token")
    transcript = None
    context = None

    # Initialize start_time for research metrics if not present
    start_time = state.get("start_time")
    if not start_time:
        start_time = datetime.now(UTC).timestamp()

    # Fetch context and state from DB if this is a re-run
    if log_id:
        try:
            async with database.async_session_maker() as session:
                result = await session.execute(select(DietaryLog).where(DietaryLog.id == log_id))
                log_entry = result.scalar_one_or_none()
                if log_entry:
                    if log_entry.description:
                        context = log_entry.description
                        logger.info(f"Using context from log {log_id}: {context[:50]}...")

                    if log_entry.transcript and not transcript:
                        transcript = log_entry.transcript
                        logger.info(f"Using persisted transcript for log {log_id}")

                    # Load persisted AMPM state
                    if log_entry.clarification_count > 0:
                        state["clarification_count"] = log_entry.clarification_count
                        logger.info(
                            f"Loaded clarification_count={log_entry.clarification_count} for log {log_id}"
                        )

                    if log_entry.ampm_data:
                        state["ampm_data"] = log_entry.ampm_data
                        logger.info(f"Loaded ampm_data for log {log_id}")
        except Exception as e:
            logger.warning(f"Failed to fetch log data from DB: {e}")

    if audio_url:
        logger.info(f"Transcribing audio from {audio_url}")
        try:
            transcript = await voice_service.transcribe_audio(audio_url, token=user_token)
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            if image_url:
                logger.warning("Audio transcription failed, but image provided. Proceeding with image only.")
                transcript = None
            else:
                raise e

    if not image_url and not transcript:
        logger.warning("No input provided for analysis")
        return {}

    logger.info("Analyzing multimodal input")
    try:
        result = await llm_service.analyze_multimodal(
            image_url=image_url,
            transcript=transcript,
            context=context,
            user_token=user_token,
            system_prompt_override=state.get("system_prompt_override"),
            provider=state.get("provider"),
            model=state.get("model"),
        )

        # Calculate deterministic complexity score
        _enrich_with_complexity(result)

        return {
            "nutritional_data": result.model_dump(),
            "overall_confidence": result.overall_confidence,
            "complexity_score": result.complexity_score,
            "complexity_breakdown": result.complexity_breakdown,
            "mandatory_clarification": result.mandatory_clarification,
            "start_time": start_time,
            "agent_turn_count": state.get("agent_turn_count", 0) + 1,
        }
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise e


async def analyze_input_streaming(
    state: AgentState,
) -> AsyncGenerator[SSEEvent | dict, None]:
    """
    Analyze input with streaming SSE events.

    Yields SSEEvent objects during processing, and finally yields
    the state update dict with nutritional_data and overall_confidence.
    """
    image_url = state.get("image_url")
    audio_url = state.get("audio_url")
    log_id = state.get("log_id")
    user_token = state.get("user_token")
    transcript = None
    context = None

    # Initialize start_time for research metrics if not present
    start_time = state.get("start_time")
    if not start_time:
        start_time = datetime.now(UTC).timestamp()

    # Fetch context and state from DB if this is a re-run
    if log_id:
        try:
            async with database.async_session_maker() as session:
                result = await session.execute(select(DietaryLog).where(DietaryLog.id == log_id))
                log_entry = result.scalar_one_or_none()
                if log_entry:
                    if log_entry.description:
                        context = log_entry.description
                        logger.info(f"Using context from log {log_id}: {context[:50]}...")

                    if log_entry.transcript and not transcript:
                        transcript = log_entry.transcript
                        logger.info(f"Using persisted transcript for log {log_id}")

                    # Load persisted AMPM state
                    if log_entry.clarification_count > 0:
                        state["clarification_count"] = log_entry.clarification_count
                        logger.info(
                            f"Loaded clarification_count={log_entry.clarification_count} for log {log_id}"
                        )

                    if log_entry.ampm_data:
                        state["ampm_data"] = log_entry.ampm_data
                        logger.info(f"Loaded ampm_data for log {log_id}")
        except Exception as e:
            logger.warning(f"Failed to fetch log data from DB: {e}")

    # Get language from state, default to Dutch
    language = state.get("language", "nl") or "nl"

    # Emit start thought
    yield SSEEvent(
        type=EVENT_THOUGHT,
        payload=AgentThought(
            step=STEP_ANALYZING,
            message=get_message("analyzing_start", language),
            timestamp=datetime.now(UTC),
        ),
    )

    language = state.get("language", "nl")

    # Process audio if provided
    if audio_url:
        logger.info(f"Transcribing audio from {audio_url} (language={language})")
        try:
            transcript = await voice_service.transcribe_audio(audio_url, language=language, token=user_token)

            # Persist transcript
            if log_id:
                try:
                    async with database.async_session_maker() as session:
                        result = await session.execute(select(DietaryLog).where(DietaryLog.id == log_id))
                        log_entry = result.scalar_one_or_none()
                        if log_entry:
                            log_entry.transcript = transcript
                            await session.commit()
                            logger.info(f"Persisted transcript for log {log_id}")
                except Exception as db_err:
                    logger.error(f"Failed to persist transcript: {db_err}")
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            if image_url:
                logger.warning("Audio transcription failed, but image provided. Proceeding with image only.")
                transcript = None
            else:
                yield SSEEvent(
                    type=EVENT_ERROR,
                    payload=AgentError(
                        code="TRANSCRIPTION_ERROR",
                        message=get_message("error_transcription", language),
                    ),
                )
                return

    if not image_url and not transcript:
        logger.warning("No input provided for analysis")
        yield SSEEvent(
            type=EVENT_ERROR,
            payload=AgentError(
                code="NO_INPUT_ERROR",
                message=get_message("error_no_input", language),
            ),
        )
        return

    try:
        logger.info("Analyzing multimodal input with streaming")

        # Token callback to emit thought events during LLM generation
        import asyncio

        token_queue = asyncio.Queue()

        async def on_token(token: str):
            await token_queue.put(("token", token))

        # Run analysis as a task so we can yield from the queue while waiting
        analysis_task = asyncio.create_task(
            llm_service.analyze_multimodal_streaming(
                image_url=image_url,
                transcript=transcript,
                context=context,
                on_token=on_token,
                user_token=user_token,
                language=language,
                system_prompt_override=state.get("system_prompt_override"),
                provider=state.get("provider"),
                model=state.get("model"),
            )
        )

        tokens_received = 0
        last_yield_count = 0

        while not analysis_task.done() or not token_queue.empty():
            try:
                # Wait for a token or timeout to check task status
                try:
                    msg_type, val = await asyncio.wait_for(token_queue.get(), timeout=1.0)
                    if msg_type == "token":
                        tokens_received += 1
                        # Yield a thought every 50 tokens to show liveness
                        if tokens_received - last_yield_count >= 50:
                            yield SSEEvent(
                                type=EVENT_THOUGHT,
                                payload=AgentThought(
                                    step=STEP_ANALYZING,
                                    message=get_message("analyzing_progress", language).format(
                                        count=tokens_received
                                    ),
                                    timestamp=datetime.now(UTC),
                                ),
                            )
                            last_yield_count = tokens_received
                            logger.info(f"Agent analysis progress: {tokens_received} tokens...")
                except TimeoutError:
                    # Just check if task is still running
                    continue
            except Exception as e:
                logger.warning(f"Error in streaming feedback loop: {e}")
                break

        # Wait for final result
        result = await analysis_task

        # Calculate deterministic complexity score
        _enrich_with_complexity(result)

        # Emit complete thought
        yield SSEEvent(
            type=EVENT_THOUGHT,
            payload=AgentThought(
                step=STEP_ANALYZING,
                message=get_message("analyzing_complete", language),
                timestamp=datetime.now(UTC),
            ),
        )

        yield {
            "nutritional_data": result.model_dump(),
            "overall_confidence": result.overall_confidence,
            "complexity_score": result.complexity_score,
            "complexity_breakdown": result.complexity_breakdown,
            "mandatory_clarification": result.mandatory_clarification,
            "start_time": start_time,
            "agent_turn_count": state.get("agent_turn_count", 0) + 1,
        }

        # Check for invalid input (non-food)
        if not result.is_food:
            logger.info(f"Input identified as non-food: {result.non_food_reason}")
            if log_id:
                try:
                    async with database.async_session_maker() as session:
                        res = await session.execute(select(DietaryLog).where(DietaryLog.id == log_id))
                        log_entry = res.scalar_one_or_none()
                        if log_entry:
                            log_entry.status = "invalid"
                            if result.non_food_reason:
                                log_entry.description = f"[Invalid]: {result.non_food_reason}"
                            await session.commit()
                            logger.info(f"Updated log {log_id} status to 'invalid'")
                except Exception as db_err:
                    logger.error(f"Failed to update log status to invalid: {db_err}")

            if log_id:
                yield SSEEvent(
                    type=EVENT_RESPONSE,
                    payload=AgentResponse(
                        log_id=str(log_id),
                        nutritional_data=result.model_dump(),
                        status="invalid",
                    ),
                )

    except Exception as e:
        logger.error(f"Analysis streaming failed: {e}")

        # Update log status to failed
        if log_id:
            try:
                async with database.async_session_maker() as session:
                    result = await session.execute(select(DietaryLog).where(DietaryLog.id == log_id))
                    log_entry = result.scalar_one_or_none()
                    if log_entry:
                        log_entry.status = "failed"
                        # Append error to description for debugging
                        current_desc = log_entry.description or ""
                        log_entry.description = f"{current_desc}\n[Analysis Failed]: {str(e)}".strip()
                        await session.commit()
                        logger.info(f"Updated log {log_id} status to 'failed'")
            except Exception as db_err:
                logger.error(f"Failed to update log status to failed: {db_err}")

        yield SSEEvent(
            type=EVENT_ERROR,
            payload=AgentError(
                code="ANALYSIS_ERROR",
                message=get_message("error_analysis", language),
            ),
        )


async def generate_clarification(state: AgentState) -> dict:
    """
    Generate a clarification question for low-confidence items.
    """
    nutritional_data = state.get("nutritional_data", {})
    items = nutritional_data.get("items", [])
    clarification_count = state.get("clarification_count", 0)

    # Find low-confidence items
    low_confidence_items = [
        FoodItem(**item) for item in items if item.get("confidence", 1.0) < CONFIDENCE_THRESHOLD
    ]

    if low_confidence_items:
        await llm_service.generate_clarification_question(
            low_confidence_items, provider=state.get("provider"), model=state.get("model")
        )
        return {
            "needs_clarification": True,
            "clarification_count": clarification_count + 1,
        }

    return {"needs_clarification": False}


async def generate_clarification_streaming(
    state: AgentState,
) -> AsyncGenerator[SSEEvent | dict, None]:
    """Generate clarification with streaming events."""
    # Get language from state, default to Dutch
    language = state.get("language", "nl") or "nl"

    yield SSEEvent(
        type=EVENT_THOUGHT,
        payload=AgentThought(
            step=STEP_CLARIFYING,
            message=get_message("clarifying", language),
            timestamp=datetime.now(UTC),
        ),
    )

    nutritional_data = state.get("nutritional_data", {})
    items = nutritional_data.get("items", [])
    clarification_count = state.get("clarification_count", 0)
    log_id = state.get("log_id")

    # Find low-confidence items
    low_confidence_items = [
        FoodItem(**item) for item in items if item.get("confidence", 1.0) < CONFIDENCE_THRESHOLD
    ]

    if low_confidence_items and log_id:
        try:
            question = await llm_service.generate_clarification_question(
                low_confidence_items, language, provider=state.get("provider"), model=state.get("model")
            )

            # Update log status to clarification in database
            async with database.async_session_maker() as session:
                result = await session.execute(select(DietaryLog).where(DietaryLog.id == log_id))
                log_entry = result.scalar_one_or_none()
                if log_entry:
                    log_entry.status = "clarification"
                    await session.commit()
                    logger.info(f"Updated log {log_id} status to 'clarification'")

            # Build context with low-confidence items for the clarification payload
            context = {
                "items": [{"name": item.name, "confidence": item.confidence} for item in low_confidence_items]
            }

            # Emit clarification event
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
                "agent_turn_count": state.get("agent_turn_count", 0) + 1,
            }
        except Exception as e:
            logger.error(f"Clarification generation failed: {e}")
            yield {"needs_clarification": False}
    else:
        yield {"needs_clarification": False}


async def check_semantic_ambiguity(state: AgentState) -> dict:
    """
    Check if any items are 'Umbrella Terms' that require immediate clarification.
    """
    nutritional_data = state.get("nutritional_data", {})
    items = nutritional_data.get("items", [])

    # Convert dict items to FoodItem objects for the service
    food_items = [FoodItem(**item) for item in items]

    unbounded_items = semantic_gatekeeper.semantic_gatekeeper.assess_lexical_boundedness(food_items)

    if unbounded_items:
        logger.info(f"Semantic Gatekeeper Interruption: Unbounded items found: {unbounded_items}")
        return {"unbounded_items": unbounded_items, "semantic_interruption_needed": True}

    return {"unbounded_items": [], "semantic_interruption_needed": False}


async def generate_semantic_clarification(state: AgentState) -> dict:
    """
    Generate a specific 'What kind of X?' question for unbounded items.
    """
    unbounded_items = state.get("unbounded_items", [])
    language = state.get("language", "nl") or "nl"
    log_id = state.get("log_id")

    if not unbounded_items:
        return {"semantic_interruption_needed": False}

    # Re-fetch items from nutritional data to get full objects
    nutritional_data = state.get("nutritional_data", {})
    all_items = [FoodItem(**item) for item in nutritional_data.get("items", [])]
    target_food_items = [item for item in all_items if item.name in unbounded_items]

    try:
        await llm_service.generate_clarification_question(
            target_food_items, language, provider=state.get("provider"), model=state.get("model")
        )

        if log_id:
            try:
                async with database.async_session_maker() as session:
                    result = await session.execute(select(DietaryLog).where(DietaryLog.id == log_id))
                    log_entry = result.scalar_one_or_none()
                    if log_entry:
                        log_entry.status = "clarification"
                        await session.commit()
                        logger.info(f"Updated log {log_id} status to 'clarification'")
            except Exception as db_err:
                logger.error(f"Failed to update log status: {db_err}")

        # Return state update
        return {
            "semantic_interruption_needed": True,
            "needs_clarification": True,
            "agent_turn_count": state.get("agent_turn_count", 0) + 1,
        }

    except Exception as e:
        logger.error(f"Semantic clarification failed: {e}")
        return {"semantic_interruption_needed": False}


async def generate_semantic_clarification_streaming(
    state: AgentState,
) -> AsyncGenerator[SSEEvent | dict, None]:
    """
    Generate semantic clarification with streaming events.
    """
    language = state.get("language", "nl") or "nl"
    unbounded_items = state.get("unbounded_items", [])
    log_id = state.get("log_id")

    if not unbounded_items:
        yield {"semantic_interruption_needed": False}
        return

    # Emit thought
    yield SSEEvent(
        type=EVENT_THOUGHT,
        payload=AgentThought(
            step=STEP_SEMANTIC_CHECK,
            message=get_message("clarifying", language),  # Reuse clarifying message or add new one
            timestamp=datetime.now(UTC),
        ),
    )

    # Generate question logic
    # TODO: Refactor llm_service to support specific semantic clarification or use rule-based
    # For now, let's just ask about the first unbounded item to keep it simple and focused

    # Simple template fallback if LLM service isn't specialized yet
    # But ideally we use LLM to be natural

    # Let's create a temporary mock or use the existing clarification generator
    # but forced on these items.

    try:
        # We need to construct FoodItems from the names for the service
        # But wait, we just have names here.
        # Let's assume we can pass a dummy FoodItem or modify the service.
        # Actually, let's just use a simple prompt for now via LLM service if possible
        # OR just reuse generate_clarification_question but ONLY for these items.

        # Re-fetch items from nutritional data to get full objects
        nutritional_data = state.get("nutritional_data", {})
        all_items = [FoodItem(**item) for item in nutritional_data.get("items", [])]
        target_food_items = [item for item in all_items if item.name in unbounded_items]

        question = await llm_service.generate_clarification_question(
            target_food_items, language, provider=state.get("provider"), model=state.get("model")
        )

        if log_id:
            async with database.async_session_maker() as session:
                result = await session.execute(select(DietaryLog).where(DietaryLog.id == log_id))
                log_entry = result.scalar_one_or_none()
                if log_entry:
                    log_entry.status = "clarification"
                    await session.commit()

        context = {
            "items": [{"name": item.name, "confidence": item.confidence} for item in target_food_items],
            "type": "semantic",  # context marker
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
            "semantic_interruption_needed": True,
            "needs_clarification": True,
            "agent_turn_count": state.get("agent_turn_count", 0) + 1,
        }

    except Exception as e:
        logger.error(f"Semantic clarification failed: {e}")
        yield {"semantic_interruption_needed": False}


async def finalize_log(state: AgentState) -> dict:
    """
    Finalize the log entry after sufficient information has been gathered.
    Updates the DietaryLog record with nutritional data and final status.
    """
    needs_review = state.get("needs_review", False)
    clarification_count = state.get("clarification_count", 0)
    overall_confidence = state.get("overall_confidence", 0.0)

    # Mark for review if confidence is still low after max attempts
    if overall_confidence < CONFIDENCE_THRESHOLD and clarification_count >= 2:
        needs_review = True

    return {
        "needs_review": needs_review,
    }


async def finalize_log_streaming(
    state: AgentState,
) -> AsyncGenerator[SSEEvent | dict, None]:
    """Finalize log with streaming events and DB persistence."""
    # Get language from state, default to Dutch
    language = state.get("language", "nl") or "nl"

    yield SSEEvent(
        type=EVENT_THOUGHT,
        payload=AgentThought(
            step=STEP_FINALIZING,
            message=get_message("finalizing", language),
            timestamp=datetime.now(UTC),
        ),
    )

    log_id = state.get("log_id")
    nutritional_data = state.get("nutritional_data", {})
    needs_review = state.get("needs_review", False)
    clarification_count = state.get("clarification_count", 0)
    overall_confidence = state.get("overall_confidence", 0.0)

    # Mark for review if confidence is still low after max attempts
    if overall_confidence < CONFIDENCE_THRESHOLD and clarification_count >= 2:
        needs_review = True

    # Persist to database
    if log_id:
        try:
            async with database.async_session_maker() as session:
                result = await session.execute(select(DietaryLog).where(DietaryLog.id == log_id))
                log_entry = result.scalar_one_or_none()

                if log_entry:
                    # Update status
                    log_entry.status = "logged"
                    log_entry.needs_review = needs_review

                    # Persist nutritional data
                    items = nutritional_data.get("items", [])
                    if items:
                        # Calculate totals from items
                        total_calories = sum(item.get("calories", 0) or 0 for item in items)
                        total_protein = sum(item.get("protein", 0) or 0 for item in items)
                        total_carbs = sum(item.get("carbs", 0) or 0 for item in items)
                        total_fats = sum(item.get("fats", 0) or 0 for item in items)

                        log_entry.calories = total_calories if total_calories > 0 else None
                        log_entry.protein = total_protein if total_protein > 0 else None
                        log_entry.carbs = total_carbs if total_carbs > 0 else None
                        log_entry.fats = total_fats if total_fats > 0 else None

                        # Extract meal_type
                        log_entry.meal_type = nutritional_data.get("meal_type")

                        # Store synthesis comment as description if not already set
                        synthesis = nutritional_data.get("synthesis_comment", "")
                        if synthesis:
                            log_entry.description = synthesis

                        # Store title
                        title = nutritional_data.get("title")
                        if title:
                            log_entry.title = title

                    await session.commit()
                    logger.info(f"Finalized log {log_id} with status='logged', needs_review={needs_review}")

                    # --- Research Metrics Persistence ---
                    try:
                        from app.models.research import ResearchLog

                        start_time = state.get("start_time")
                        current_time = datetime.now(UTC).timestamp()
                        processing_time_ms = int((current_time - start_time) * 1000) if start_time else 0

                        # Determine input modality
                        image_url = state.get("image_url")
                        audio_url = state.get("audio_url")
                        modality = "unknown"
                        if image_url and audio_url:
                            modality = "multimodal"
                        elif image_url:
                            modality = "photo"
                        elif audio_url:
                            modality = "voice"

                        # Get complexity data from state/result
                        complexity_score = state.get("complexity_score")
                        complexity_breakdown = state.get("complexity_breakdown")
                        dominant_factor = (
                            complexity_breakdown.dominant_factor if complexity_breakdown else None
                        )

                        research_log = ResearchLog(
                            log_id=log_id,
                            input_modality=modality,
                            processing_time_ms=processing_time_ms,
                            agent_turns_count=state.get("agent_turn_count", 1),
                            was_corrected=clarification_count > 0,
                            confidence_score=overall_confidence,
                            complexity_score=complexity_score,
                            dominant_factor=dominant_factor,
                        )
                        session.add(research_log)
                        await session.commit()
                        logger.info(f"Persisted research metrics for log {log_id}")
                    except Exception as research_err:
                        logger.error(f"Failed to persist research metrics: {research_err}")
                    # -----------------------------------

        except Exception as e:
            logger.error(f"Failed to persist finalized log: {e}")

    # Emit final response event
    if log_id:
        yield SSEEvent(
            type=EVENT_RESPONSE,
            payload=AgentResponse(
                log_id=str(log_id),
                nutritional_data=nutritional_data,
                status="logged" if not needs_review else "needs_review",
            ),
        )

    yield {
        "needs_review": needs_review,
    }
