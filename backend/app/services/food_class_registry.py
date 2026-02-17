import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RiskProfile(BaseModel):
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
            self._default_profile = RiskProfile(**default_data)

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
        Should handle partial matching or lemmatization in future,
        currently does exact match on aliases.
        """
        if not food_name:
            return None

        normalized_name = food_name.lower().strip()

        # Direct match in alias map
        if normalized_name in self._alias_map:
            return self._alias_map[normalized_name]

        # Check if any alias is a substring of the food name (simple fuzzy match)
        # e.g. "vegan burger" contains "burger"
        # We prioritize longer matches (e.g. "cheeseburger" over "burger" if both exist)
        # But here we just check if a known alias is part of the name

        # Sort aliases by length descending to match specificity first
        sorted_aliases = sorted(self._alias_map.keys(), key=len, reverse=True)
        for alias in sorted_aliases:
            # Check for word boundary match to avoid false positives (e.g. "ham" in "hamburger")
            # For simplicity in MVP, just checking substring with spaces or exact bounds
            if f" {alias} " in f" {normalized_name} ":
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
            return RiskProfile(**profile_data)

        if self._default_profile:
            return self._default_profile

        # Hard fallback if file load failed completely
        return RiskProfile(
            weights={"ingredients": 0.5, "prep": 0.5, "volume": 0.5},
            semantic_penalty=0.0,
            mandatory_clarification=False,
            is_umbrella_term=False,
        )


# Global singleton instance
registry = FoodClassRegistry()
