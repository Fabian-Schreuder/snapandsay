from sqlalchemy.orm import DeclarativeBase

# Import models to ensure they are registered with Base.metadata
from .log import DietaryLog  # noqa: F401
from .research import ResearchLog  # noqa: F401


class Base(DeclarativeBase):
    pass
