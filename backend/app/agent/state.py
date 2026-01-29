from typing import Annotated, Any, TypedDict
from uuid import UUID

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    The state of the agent.

    Core input fields:
        messages: Annotated list of messages with add_messages reducer
        image_url: URL to the uploaded food image
        audio_url: URL to the uploaded voice description audio

    Analysis output fields:
        nutritional_data: Extracted food items and nutritional estimates
        log_id: UUID of the DietaryLog record being processed

    Confidence routing fields:
        overall_confidence: Average confidence score across detected items (0-1)
        clarification_count: Number of clarification questions asked so far
        needs_clarification: Whether the agent needs to ask a follow-up question
        needs_review: Whether the log should be flagged for human review
    """

    messages: Annotated[list[BaseMessage], add_messages]
    image_url: str | None
    audio_url: str | None
    nutritional_data: dict[str, Any] | None
    log_id: UUID | None
    overall_confidence: float
    clarification_count: int
    needs_clarification: bool
    needs_review: bool
    user_token: str | None

    # Research Metrics
    start_time: float | None  # Timestamp when analysis started
    agent_turn_count: int  # Total agent responses generated

    # Localization
    language: str | None  # User's preferred language code (e.g., "nl", "en")

    # Research/Experimentation
    system_prompt_override: str | None
