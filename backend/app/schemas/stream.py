"""Stream analysis request schemas."""
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field


class StreamAnalysisRequest(BaseModel):
    """Request schema for initiating a streaming analysis."""

    log_id: UUID = Field(..., description="Log ID from /upload response")
    image_path: Optional[str] = Field(None, description="Path to uploaded image")
    audio_path: Optional[str] = Field(None, description="Path to uploaded audio")
