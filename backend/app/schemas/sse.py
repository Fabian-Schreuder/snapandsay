"""SSE event schemas for agent streaming responses."""
from datetime import datetime
from typing import Literal, Any

from pydantic import BaseModel, Field


class AgentThought(BaseModel):
    """Schema for agent thought events during processing."""

    step: str = Field(..., description="Current processing step identifier")
    message: str = Field(..., description="Human-readable thought message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When this thought was generated"
    )


class AgentResponse(BaseModel):
    """Schema for final agent response event."""

    log_id: str = Field(..., description="UUID of the created dietary log")
    nutritional_data: dict[str, Any] = Field(
        ..., description="Extracted nutritional information"
    )
    status: str = Field(default="success", description="Processing status")


class AgentError(BaseModel):
    """Schema for agent error events."""

    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-friendly error message")


class SSEEvent(BaseModel):
    """Base SSE event wrapper with type discrimination."""

    type: Literal["agent.thought", "agent.response", "agent.error"] = Field(
        ..., description="Event type for frontend routing"
    )
    payload: AgentThought | AgentResponse | AgentError = Field(
        ..., description="Event payload data"
    )
