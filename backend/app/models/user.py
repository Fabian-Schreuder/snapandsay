from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID

from . import Base


class User(Base):
    """User model mapping to public.users table."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)
    anonymous_id = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
