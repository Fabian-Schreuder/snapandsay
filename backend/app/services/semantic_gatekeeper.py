import logging

from app.schemas.analysis import FoodItem
from app.services.food_class_registry import registry

logger = logging.getLogger(__name__)


class SemanticGatekeeper:
    """
    Enforces the 'Semantic Gatekeeper Pattern' (Architecture Decision 3).

    Responsible for identifying 'Umbrella Terms' (e.g., 'Sandwich', 'Salad')
    that require immediate clarification before any complexity analysis or
    ingredient guessing can occur.
    """

    @staticmethod
    def assess_lexical_boundedness(food_items: list[FoodItem]) -> list[str]:
        """
        id checks each food item against the FoodClassRegistry to see if it
        is an 'Umbrella Term'.

        Args:
            food_items: List of detected food items.

        Returns:
            List of names of items that are semantically unbounded (umbrella terms).
        """
        unbounded_items = []

        for item in food_items:
            # Registry lookup
            risk_profile = registry.get_risk_profile(item.name)

            if risk_profile.is_umbrella_term:
                logger.info(f"Semantic Gatekeeper: '{item.name}' detected as Umbrella Term.")
                unbounded_items.append(item.name)

        return unbounded_items


# Global instance
semantic_gatekeeper = SemanticGatekeeper()
