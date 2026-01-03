"""SSE event schemas for agent streaming responses."""

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AgentThought(BaseModel):
    """Schema for agent thought events during processing."""

    step: str = Field(..., description="Current processing step identifier")
    message: str = Field(..., description="Human-readable thought message")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When this thought was generated"
    )


class AgentResponse(BaseModel):
    """Schema for final agent response event."""

    log_id: str = Field(..., description="UUID of the created dietary log")
    nutritional_data: dict[str, Any] = Field(..., description="Extracted nutritional information")
    status: str = Field(default="success", description="Processing status")


class AgentError(BaseModel):
    """Schema for agent error events."""

    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-friendly error message")


class AgentClarification(BaseModel):
    """Schema for agent clarification question events."""

    question: str = Field(..., description="Clarification question text")
    options: list[str] = Field(
        default_factory=list,
        description="Suggested answer options for quick selection",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Low-confidence item details for context",
    )
    log_id: UUID = Field(..., description="Log ID for clarification response endpoint")


class SSEEvent(BaseModel):
    """Base SSE event wrapper with type discrimination."""

    type: Literal["agent.thought", "agent.response", "agent.error", "agent.clarification"] = Field(
        ..., description="Event type for frontend routing"
    )
    payload: AgentThought | AgentResponse | AgentError | AgentClarification = Field(
        ..., description="Event payload data"
    )
