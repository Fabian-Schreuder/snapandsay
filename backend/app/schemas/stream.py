"""Stream analysis request schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class StreamAnalysisRequest(BaseModel):
    """Request schema for initiating a streaming analysis."""

    log_id: UUID = Field(..., description="Log ID from /upload response")
    image_path: str | None = Field(None, description="Path to uploaded image")
    audio_path: str | None = Field(None, description="Path to uploaded audio")
    language: str = Field(default="nl", description="Language code for agent responses")
    clinical_threshold: float = Field(
        default=15.0, description="Complexity threshold for routing to clarification (lower = more sensitive)"
    )
    confidence_threshold: float = Field(
        default=0.85, description="Confidence threshold for skipping clarification"
    )
    system_prompt_override: str | None = Field(
        None, description="Optional system prompt to use for experiments"
    )
    provider: str | None = Field(None, description="LLM provider (openai, google)")
    model: str | None = Field(None, description="Specific model name to use")
    force_clarify: bool = Field(False, description="Internal test flag: always force clarification")
    force_finalize: bool = Field(False, description="Internal test flag: always skip clarification")
