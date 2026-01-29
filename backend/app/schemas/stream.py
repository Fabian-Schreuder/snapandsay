"""Stream analysis request schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class StreamAnalysisRequest(BaseModel):
    """Request schema for initiating a streaming analysis."""

    log_id: UUID = Field(..., description="Log ID from /upload response")
    image_path: str | None = Field(None, description="Path to uploaded image")
    audio_path: str | None = Field(None, description="Path to uploaded audio")
    language: str = Field(default="nl", description="Language code for agent responses")
    system_prompt_override: str | None = Field(
        None, description="Optional system prompt to use for experiments"
    )
