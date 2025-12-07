from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID


class AnalysisUploadRequest(BaseModel):
    image_path: str
    audio_path: Optional[str] = None
    client_timestamp: str


class AnalysisUploadResponse(BaseModel):
    log_id: UUID
    status: str


class FoodItem(BaseModel):
    name: str = Field(..., description="Name of the food item")
    quantity: str = Field(..., description="Quantity or portion size")
    calories: Optional[int] = Field(None, description="Estimated calories")
    confidence: float = Field(..., description="Confidence score between 0 and 1")


class AnalysisResult(BaseModel):
    """Result of analyzing food image/audio input."""
    items: List[FoodItem] = Field(..., description="List of identified food items")
    synthesis_comment: str = Field(..., description="Overall summary or analysis comment")

    @property
    def overall_confidence(self) -> float:
        """Compute overall confidence as simple average of item confidences."""
        if not self.items:
            return 0.0
        return sum(item.confidence for item in self.items) / len(self.items)


class ClarifyRequest(BaseModel):
    """Request body for clarification response endpoint."""

    response: str = Field(..., description="User's clarification response text")
    is_voice: bool = Field(
        default=False, description="Whether response came from voice input"
    )
