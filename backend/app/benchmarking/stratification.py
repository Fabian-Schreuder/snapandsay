"""
Stratification Engine for Oracle Benchmarking.

Classifies Nutrition5k dishes into 'simple' or 'complex' categories
based on multiple factors as per research methodology requirements.
"""

from dataclasses import dataclass

from app.benchmarking.schemas import NutritionDish


@dataclass
class StratificationScores:
    """Individual scores for each stratification factor."""

    ingredient_count: float  # 0.0 (simple) to 1.0 (complex)
    visual_distinctiveness: float  # 0.0 (high/simple) to 1.0 (low/complex)
    caloric_density: float  # 0.0 (low/simple) to 1.0 (high/complex)
    ambiguity: float  # 0.0 (low/simple) to 1.0 (high/complex)

    @property
    def weighted_average(self) -> float:
        """Calculate weighted average of all scores."""
        weights = {
            "ingredient_count": 0.35,
            "visual_distinctiveness": 0.25,
            "caloric_density": 0.20,
            "ambiguity": 0.20,
        }
        return (
            self.ingredient_count * weights["ingredient_count"]
            + self.visual_distinctiveness * weights["visual_distinctiveness"]
            + self.caloric_density * weights["caloric_density"]
            + self.ambiguity * weights["ambiguity"]
        )


# Keyword sets for heuristic classification
MIXED_DISH_KEYWORDS = frozenset(
    {
        "sauce",
        "dressing",
        "gravy",
        "casserole",
        "stew",
        "soup",
        "curry",
        "blend",
        "puree",
        "mash",
        "stuffed",
        "layered",
        "baked",
        "fried",
        "coated",
        "breaded",
        "glazed",
        "cream",
        "butter",
        "oil",
        "mayo",
        "mayonnaise",
        "paste",
        "spread",
    }
)

DISTINCT_ITEM_KEYWORDS = frozenset(
    {
        "apple",
        "banana",
        "orange",
        "grape",
        "strawberry",
        "blueberry",
        "melon",
        "watermelon",
        "carrot",
        "broccoli",
        "cauliflower",
        "tomato",
        "lettuce",
        "cucumber",
        "pepper",
        "egg",
        "eggs",
        "chicken",
        "beef",
        "pork",
        "fish",
        "salmon",
        "tuna",
        "shrimp",
        "rice",
        "bread",
        "toast",
        "potato",
        "corn",
        "beans",
        "nuts",
        "almonds",
        "walnuts",
        "cheese",
        "yogurt",
        "milk",
    }
)


class StratificationEngine:
    """
    Multi-factor stratification engine for Nutrition5k dishes.

    Classifies dishes as 'simple' or 'complex' based on:
    - Ingredient count (<=3 = simple)
    - Visual distinctiveness (separate items = simple)
    - Caloric density (<=150 kcal/100g = simple)
    - Ambiguity score (distinct ingredients = simple)
    """

    # Thresholds
    SIMPLE_INGREDIENT_THRESHOLD = 3
    HIGH_CALORIC_DENSITY_THRESHOLD = 150.0  # kcal per 100g
    COMPLEXITY_THRESHOLD = 0.35  # Score above this = complex

    def ingredient_count_score(self, dish: NutritionDish) -> float:
        """
        Score based on ingredient count.
        Returns 0.0 for <=3 ingredients, scaling up to 1.0 for 10+ ingredients.
        """
        count = len(dish.ingredients)
        if count <= self.SIMPLE_INGREDIENT_THRESHOLD:
            return 0.0
        elif count >= 10:
            return 1.0
        else:
            # Linear interpolation between 3 and 10
            return (count - self.SIMPLE_INGREDIENT_THRESHOLD) / (10 - self.SIMPLE_INGREDIENT_THRESHOLD)

    def visual_distinctiveness_score(self, dish: NutritionDish) -> float:
        """
        Heuristic score for visual distinctiveness.
        Low score (0.0) = high distinctiveness (separate, visible items)
        High score (1.0) = low distinctiveness (mixed, layered)

        Uses keyword matching on ingredient names.
        """
        if not dish.ingredients:
            return 0.5  # Unknown, return middle score

        ingredient_names = " ".join(i.name.lower() for i in dish.ingredients)

        # Count mixed dish indicators
        mixed_count = sum(1 for kw in MIXED_DISH_KEYWORDS if kw in ingredient_names)

        # Count distinct item indicators
        distinct_count = sum(1 for kw in DISTINCT_ITEM_KEYWORDS if kw in ingredient_names)

        # Calculate ratio
        total = mixed_count + distinct_count
        if total == 0:
            return 0.0  # No complexity-indicating keywords → treat as simple

        # More mixed = higher score (less distinct)
        return mixed_count / total

    def caloric_density_score(self, dish: NutritionDish) -> float:
        """
        Score based on caloric density (kcal per 100g).
        Low density (<= 150 kcal/100g) = simple (0.0)
        High density (> 300 kcal/100g) = complex (1.0)
        """
        if dish.total_mass <= 0:
            return 0.5  # Unknown

        density = (dish.total_calories / dish.total_mass) * 100

        if density <= self.HIGH_CALORIC_DENSITY_THRESHOLD:
            return 0.0
        elif density >= 300:
            return 1.0
        else:
            # Linear interpolation between 150 and 300
            return (density - self.HIGH_CALORIC_DENSITY_THRESHOLD) / (
                300 - self.HIGH_CALORIC_DENSITY_THRESHOLD
            )

    def ambiguity_score(self, dish: NutritionDish) -> float:
        """
        Score based on ingredient ambiguity.
        Sauces, dressings, and mixed items increase ambiguity.
        """
        if not dish.ingredients:
            return 0.5

        ambiguous_count = 0
        for ingredient in dish.ingredients:
            name_lower = ingredient.name.lower()
            # Check for ambiguous ingredient patterns
            if any(
                kw in name_lower
                for kw in ["sauce", "dressing", "mixed", "various", "assorted", "other", "unknown"]
            ):
                ambiguous_count += 1

        # Score based on proportion of ambiguous ingredients
        return min(1.0, ambiguous_count / len(dish.ingredients) * 2)

    def get_scores(self, dish: NutritionDish) -> StratificationScores:
        """Calculate all stratification scores for a dish."""
        return StratificationScores(
            ingredient_count=self.ingredient_count_score(dish),
            visual_distinctiveness=self.visual_distinctiveness_score(dish),
            caloric_density=self.caloric_density_score(dish),
            ambiguity=self.ambiguity_score(dish),
        )

    def classify(self, dish: NutritionDish) -> str:
        """
        Classify a dish as 'simple' or 'complex' based on weighted scores.
        """
        scores = self.get_scores(dish)
        weighted = scores.weighted_average

        return "complex" if weighted >= self.COMPLEXITY_THRESHOLD else "simple"
