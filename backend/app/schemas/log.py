"""Schemas for dietary log API responses."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class DietaryLogResponse(BaseModel):
    """Response schema for a single dietary log entry."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    status: str
    image_path: str
    transcript: Optional[str] = None
    description: Optional[str] = None
    calories: Optional[int] = None
    protein: Optional[int] = None
    carbs: Optional[int] = None
    fats: Optional[int] = None
    meal_type: Optional[str] = None
    needs_review: bool
    created_at: datetime


class DietaryLogUpdateRequest(BaseModel):
    """Request schema for updating a dietary log entry."""
    description: Optional[str] = Field(None, max_length=500)
    calories: Optional[int] = Field(None, ge=0, le=5000)
    protein: Optional[int] = Field(None, ge=0, le=500)
    carbs: Optional[int] = Field(None, ge=0, le=500)
    fats: Optional[int] = Field(None, ge=0, le=500)


class LogListMeta(BaseModel):
    """Metadata for log list response."""
    total: int


class DietaryLogListResponse(BaseModel):
    """Response schema for list of dietary logs."""
    data: List[DietaryLogResponse]
    meta: LogListMeta
