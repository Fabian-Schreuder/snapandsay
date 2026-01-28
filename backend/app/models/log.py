import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from . import Base
from .user import User  # noqa: F401


class DietaryLog(Base):
    """Dietary log entry for tracking user meals."""

    __tablename__ = "dietary_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    user = relationship("User", backref="logs")

    # Media
    image_path = Column(String, nullable=False)
    audio_path = Column(String, nullable=True)

    # Analysis
    transcript = Column(String, nullable=True)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)

    # Nutrition
    calories = Column(Integer, nullable=True)
    protein = Column(Integer, nullable=True)
    carbs = Column(Integer, nullable=True)
    fats = Column(Integer, nullable=True)
    meal_type = Column(String, nullable=True)

    # Status
    status = Column(
        Enum("processing", "clarification", "logged", "failed", "invalid", name="log_status_enum"),
        default="processing",
        nullable=False,
    )
    needs_review = Column(Boolean, default=False, nullable=False)

    # Metadata
    client_timestamp = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
