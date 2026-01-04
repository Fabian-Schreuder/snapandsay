from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models to ensure they are registered with Base.metadata
from .log import DietaryLog  # noqa: F401, E402
from .research import ResearchLog  # noqa: F401, E402
