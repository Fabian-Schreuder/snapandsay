import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship

from . import Base


class ResearchLog(Base):
    """
    Research metrics validation log.
    Tracks latency, friction (turns), and error correction for research analysis.
    One-to-One relationship with DietaryLog.
    """

    __tablename__ = "research_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    log_id = Column(
        UUID(as_uuid=True), ForeignKey("dietary_logs.id"), nullable=False, unique=True, index=True
    )

    # Research Metrics
    input_modality = Column(String, nullable=False)  # 'voice', 'photo', 'text'
    processing_time_ms = Column(Integer, nullable=False)
    agent_turns_count = Column(Integer, nullable=False)
    was_corrected = Column(Boolean, default=False, nullable=False)
    confidence_score = Column(Float, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    dietary_log = relationship(
        "DietaryLog",
        backref=backref("research_log", cascade="all, delete-orphan", uselist=False),
    )
