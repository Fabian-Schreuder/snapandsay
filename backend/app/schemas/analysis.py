from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class AnalysisUploadRequest(BaseModel):
    image_path: str | None = None
    audio_path: str | None = None
    text_input: str | None = None
    client_timestamp: str

    @model_validator(mode="after")
    def check_input_exists(self) -> Self:
        if not self.image_path and not self.text_input:
            raise ValueError("Either image_path or text_input must be provided")
        return self


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


class AmbiguityLevels(BaseModel):
    hidden_ingredients: int = Field(ge=0, le=3, description="0 (Visible) to 3 (Black Box)")
    invisible_prep: int = Field(ge=0, le=3, description="0 (None) to 3 (Extensive)")
    portion_ambiguity: int = Field(ge=0, le=3, description="0 (Known) to 3 (Unknown)")


class ComplexityBreakdown(BaseModel):
    levels: AmbiguityLevels
    weights: dict[str, float] | None = Field(
        None, description="Weights used for calculation (populated by Gatekeeper)"
    )
    semantic_penalty: float = Field(
        0.0,
        description="Semantic penalty from food class risk profile (0.0-4.0, see food_class_registry.yaml)",
    )
    dominant_factor: str | None = Field(None, description="Factor driving the complexity score")
    score: float = Field(
        ...,
        description="Calculated complexity score (deterministic scale, practical range 0.0-~21.1)",
    )


class AnalysisResult(BaseModel):
    """Result of analyzing food image/audio input."""

    title: str = Field(..., description="Short, descriptive title of the meal (e.g. 'Roasted Cashews')")
    items: list[FoodItem] = Field(..., description="List of identified food items")
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] | None = Field(
        None, description="Type of meal (breakfast, lunch, dinner, snack)"
    )
    synthesis_comment: str = Field(..., description="Overall summary or analysis comment")

    # Validation
    is_food: bool = Field(False, description="Whether the input is a valid food/drink item")
    non_food_reason: str | None = Field(None, description="Reason why input is not food (if is_food=False)")
    mandatory_clarification: bool = Field(
        False, description="Whether the food class requires mandatory clarification (from Registry)"
    )

    # AMPM complexity rating
    complexity_score: float = Field(
        0.0,
        description=(
            "Deterministic meal complexity score (C = Σ(w·L²) + P_sem). "
            "Range 0.0-~21.1 depending on food class risk profile. "
            "Higher values indicate greater ambiguity requiring clarification. "
            "Clinical routing threshold default: 15.0."
        ),
    )

    # Structured Ambiguity Analysis (Phase 1)
    complexity_breakdown: ComplexityBreakdown | None = Field(
        None, description="Structured breakdown of complexity factors"
    )

    @property
    def overall_confidence(self) -> float:
        """Compute overall confidence as simple average of item confidences."""
        if not self.items:
            return 0.0
        return sum(item.confidence for item in self.items) / len(self.items)


class ClarifyResponse(BaseModel):
    """A single clarification answer for one food item."""

    item_name: str = Field(default="", description="Name of the food item this response is for")
    response: str = Field(..., description="User's clarification response text")
    is_voice: bool = Field(default=False, description="Whether response came from voice input")
    audio_path: str | None = Field(
        default=None, description="Supabase Storage path for voice audio to transcribe"
    )


class ClarifyRequest(BaseModel):
    """Request body for clarification response endpoint (supports batch)."""

    responses: list[ClarifyResponse] = Field(
        ..., description="List of clarification responses (one per question)"
    )
