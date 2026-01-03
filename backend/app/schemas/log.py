"""Schemas for dietary log API responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DietaryLogResponse(BaseModel):
    """Response schema for a single dietary log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    status: str
    image_path: str
    image_url: str | None = None
    title: str | None = None
    transcript: str | None = None
    description: str | None = None
    calories: int | None = None
    protein: int | None = None
    carbs: int | None = None
    fats: int | None = None
    meal_type: str | None = None
    needs_review: bool
    created_at: datetime


class DietaryLogUpdateRequest(BaseModel):
    """Request schema for updating a dietary log entry."""

    title: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    calories: int | None = Field(None, ge=0, le=5000)
    protein: int | None = Field(None, ge=0, le=500)
    carbs: int | None = Field(None, ge=0, le=500)
    fats: int | None = Field(None, ge=0, le=500)


class LogListMeta(BaseModel):
    """Metadata for log list response."""

    total: int


class DietaryLogListResponse(BaseModel):
    """Response schema for list of dietary logs."""

    data: list[DietaryLogResponse]
    meta: LogListMeta
