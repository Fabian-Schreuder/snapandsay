import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RiskProfile(BaseModel):
    name: str
    weights: dict[str, float]
    semantic_penalty: float
    mandatory_clarification: bool
    is_umbrella_term: bool


class FoodClassRegistry:
    _instance = None
    _registry: dict[str, Any] = {}
    _alias_map: dict[str, str] = {}
    _default_profile: RiskProfile | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_registry()
        return cls._instance

    def _load_registry(self):
        """Loads the YAML registry from disk."""
        try:
            # Path relative to this file: ../agent/data/food_class_registry.yaml
            # Assuming this file is in backend/app/services/
            base_dir = Path(__file__).resolve().parent.parent
            registry_path = base_dir / "agent" / "data" / "food_class_registry.yaml"

            if not registry_path.exists():
                logger.error(f"Registry file not found at {registry_path}")
                return

            with open(registry_path) as f:
                data = yaml.safe_load(f)

            if not data:
                logger.warning("Registry file is empty")
                return

            # Load default profile
            default_data = data.get("default", {})
            self._default_profile = RiskProfile(name="default", **default_data)

            # Load classes and build alias map
            classes = data.get("classes", {})
            self._registry = classes

            self._alias_map = {}
            for class_key, class_data in classes.items():
                aliases = class_data.get("aliases", [])
                # Map the class key itself
                self._alias_map[class_key.lower()] = class_key
                # Map all aliases
                for alias in aliases:
                    self._alias_map[alias.lower()] = class_key

            logger.info(
                f"Loaded {len(classes)} food classes and {len(self._alias_map)} aliases into registry"
            )

        except Exception as e:
            logger.error(f"Failed to load food class registry: {e}")

    def lookup(self, food_name: str) -> str | None:
        """
        Looks up a food name in the registry (case-insensitive).
        Returns the canonical class key if found, else None.
        Handles exact matches, and compound words / plurals using regex.
        """
        if not food_name:
            return None

        normalized_name = food_name.lower().strip()

        # Direct match in alias map
        if normalized_name in self._alias_map:
            return self._alias_map[normalized_name]

        # Use regex to find if any alias is the base word (suffix) of the item.
        # This handles compound words (e.g. "runderburger" ending in "burger", "sojamelk" ending in "melk")
        # and plurals/diminutives ("burgers", "broodje").
        # We sort aliases by length descending to match specificity first
        # (e.g. "cheeseburger" before "burger").
        sorted_aliases = sorted(self._alias_map.keys(), key=len, reverse=True)

        import re

        for alias in sorted_aliases:
            # Pattern: alias followed by optional plural/diminutive endings, at a word boundary
            pattern = r"(?i)" + re.escape(alias) + r"(s|en|je|jes)?\b"
            if re.search(pattern, normalized_name):
                return self._alias_map[alias]

        return None

    def get_risk_profile(self, food_name: str) -> RiskProfile:
        """
        Returns the risk profile for a given food name.
        Falls back to default if not found.
        """
        class_key = self.lookup(food_name)

        if class_key and class_key in self._registry:
            data = self._registry[class_key]
            # Exclude 'aliases' from the model dump passed to RiskProfile
            # (RiskProfile definition above doesn't have aliases field for lightweight passing)
            profile_data = {k: v for k, v in data.items() if k != "aliases"}
            return RiskProfile(name=class_key, **profile_data)

        if self._default_profile:
            return self._default_profile

        # Hard fallback if file load failed completely
        return RiskProfile(
            name="fallback",
            weights={"ingredients": 0.5, "prep": 0.5, "volume": 0.5},
            semantic_penalty=0.0,
            mandatory_clarification=False,
            is_umbrella_term=False,
        )


# Global singleton instance
registry = FoodClassRegistry()
