from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisUploadRequest(BaseModel):
    image_path: str
    audio_path: str | None = None
    client_timestamp: str


class AnalysisUploadResponse(BaseModel):
    log_id: UUID
    status: str


class FoodItem(BaseModel):
    name: str = Field(..., description="Name of the food item")
    quantity: str = Field(..., description="Quantity or portion size")
    calories: int | None = Field(None, description="Estimated calories")
    protein: int | None = Field(None, description="Estimated protein in grams")
    carbs: int | None = Field(None, description="Estimated carbohydrates in grams")
    fats: int | None = Field(None, description="Estimated fats in grams")
    confidence: float = Field(..., description="Confidence score between 0 and 1")


class AnalysisResult(BaseModel):
    """Result of analyzing food image/audio input."""

    title: str = Field(..., description="Short, descriptive title of the meal (e.g. 'Roasted Cashews')")
    items: list[FoodItem] = Field(..., description="List of identified food items")
    meal_type: str | None = Field(None, description="Type of meal (e.g., Breakfast, Lunch, Dinner, Snack)")
    synthesis_comment: str = Field(..., description="Overall summary or analysis comment")

    # Validation
    is_food: bool = Field(False, description="Whether the input is a valid food/drink item")
    non_food_reason: str | None = Field(None, description="Reason why input is not food (if is_food=False)")

    # AMPM complexity rating
    complexity_score: float = Field(
        0.0,
        description=(
            "Meal complexity from 0.0 (simple, single item) to 1.0 (complex, multi-component). "
            "Consider: number of distinct items, composite dishes, ambiguous portions, mixed preparations."
        ),
    )

    @property
    def overall_confidence(self) -> float:
        """Compute overall confidence as simple average of item confidences."""
        if not self.items:
            return 0.0
        return sum(item.confidence for item in self.items) / len(self.items)


class ClarifyRequest(BaseModel):
    """Request body for clarification response endpoint."""

    response: str = Field(..., description="User's clarification response text")
    is_voice: bool = Field(default=False, description="Whether response came from voice input")
