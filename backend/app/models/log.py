import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from . import Base

class DietaryLog(Base):
    __tablename__ = "dietary_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Media
    image_path = Column(String, nullable=False)
    audio_path = Column(String, nullable=True)
    
    # Analysis
    transcript = Column(String, nullable=True)
    description = Column(String, nullable=True)
    
    # Nutrition
    calories = Column(Integer, nullable=True)
    protein = Column(Integer, nullable=True)
    carbs = Column(Integer, nullable=True)
    fats = Column(Integer, nullable=True)
    
    # Status
    status = Column(Enum("processing", "clarification", "logged", name="log_status_enum"), default="processing", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
