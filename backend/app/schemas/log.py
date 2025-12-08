"""Schemas for dietary log API responses."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class DietaryLogResponse(BaseModel):
    """Response schema for a single dietary log entry."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    image_path: str
    transcript: Optional[str] = None
    description: Optional[str] = None
    calories: Optional[int] = None
    protein: Optional[int] = None
    carbs: Optional[int] = None
    fats: Optional[int] = None
    needs_review: bool
    created_at: datetime


class LogListMeta(BaseModel):
    """Metadata for log list response."""
    total: int


class DietaryLogListResponse(BaseModel):
    """Response schema for list of dietary logs."""
    data: List[DietaryLogResponse]
    meta: LogListMeta
