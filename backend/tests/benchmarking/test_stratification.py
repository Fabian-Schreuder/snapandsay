"""
Unit tests for Stratification Engine.
"""

import pytest

from app.benchmarking.schemas import IngredientInfo, NutritionDish
from app.benchmarking.stratification import StratificationEngine, StratificationScores


@pytest.fixture
def engine():
    return StratificationEngine()


@pytest.fixture
def simple_dish():
    """A simple dish: <= 3 ingredients, distinct items, low caloric density."""
    return NutritionDish(
        dish_id="simple_001",
        total_calories=150,
        total_mass=200,  # 75 kcal/100g - low density
        total_fat=5,
        total_carb=20,
        total_protein=10,
        ingredients=[
            IngredientInfo(id="1", name="apple", grams=100),
            IngredientInfo(id="2", name="banana", grams=80),
        ],
        complexity="pending",
    )


@pytest.fixture
def complex_dish():
    """A complex dish: many ingredients, sauces, high caloric density."""
    return NutritionDish(
        dish_id="complex_001",
        total_calories=800,
        total_mass=250,  # 320 kcal/100g - high density
        total_fat=45,
        total_carb=50,
        total_protein=35,
        ingredients=[
            IngredientInfo(id="1", name="pasta", grams=150),
            IngredientInfo(id="2", name="cream sauce", grams=80),
            IngredientInfo(id="3", name="cheese", grams=50),
            IngredientInfo(id="4", name="butter", grams=30),
            IngredientInfo(id="5", name="garlic", grams=10),
            IngredientInfo(id="6", name="mixed herbs", grams=5),
        ],
        complexity="pending",
    )


@pytest.fixture
def edge_dish():
    """Edge case: exactly 3 ingredients, moderate density."""
    return NutritionDish(
        dish_id="edge_001",
        total_calories=300,
        total_mass=200,  # 150 kcal/100g - threshold
        total_fat=10,
        total_carb=40,
        total_protein=15,
        ingredients=[
            IngredientInfo(id="1", name="rice", grams=100),
            IngredientInfo(id="2", name="chicken", grams=80),
            IngredientInfo(id="3", name="broccoli", grams=50),
        ],
        complexity="pending",
    )


class TestIngredientCountScore:
    """Tests for ingredient count scoring."""

    def test_simple_dish_low_score(self, engine, simple_dish):
        """2 ingredients should score 0.0 (simple)."""
        score = engine.ingredient_count_score(simple_dish)
        assert score == 0.0

    def test_complex_dish_high_score(self, engine, complex_dish):
        """6 ingredients should score > 0.0."""
        score = engine.ingredient_count_score(complex_dish)
        assert 0.0 < score < 1.0

    def test_edge_dish_at_threshold(self, engine, edge_dish):
        """Exactly 3 ingredients should score 0.0."""
        score = engine.ingredient_count_score(edge_dish)
        assert score == 0.0

    def test_ten_plus_ingredients_max_score(self, engine):
        """10+ ingredients should score 1.0."""
        dish = NutritionDish(
            dish_id="many",
            total_calories=500,
            total_mass=300,
            total_fat=20,
            total_carb=60,
            total_protein=25,
            ingredients=[IngredientInfo(id=str(i), name=f"item_{i}", grams=30) for i in range(12)],
            complexity="pending",
        )
        score = engine.ingredient_count_score(dish)
        assert score == 1.0


class TestVisualDistinctivenessScore:
    """Tests for visual distinctiveness scoring using keyword heuristics."""

    def test_distinct_items_low_score(self, engine, simple_dish):
        """Apple and banana are visually distinct."""
        score = engine.visual_distinctiveness_score(simple_dish)
        assert score < 0.5  # Should be low (distinct = simple)

    def test_mixed_dish_high_score(self, engine, complex_dish):
        """Cream sauce and butter indicate mixing."""
        score = engine.visual_distinctiveness_score(complex_dish)
        assert score > 0.0  # Should indicate some mixing

    def test_empty_ingredients(self, engine):
        """Empty ingredients should return middle score."""
        dish = NutritionDish(
            dish_id="empty",
            total_calories=0,
            total_mass=0,
            total_fat=0,
            total_carb=0,
            total_protein=0,
            ingredients=[],
            complexity="pending",
        )
        score = engine.visual_distinctiveness_score(dish)
        assert score == 0.5


class TestCaloricDensityScore:
    """Tests for caloric density scoring."""

    def test_low_density_low_score(self, engine, simple_dish):
        """75 kcal/100g is below threshold."""
        score = engine.caloric_density_score(simple_dish)
        assert score == 0.0

    def test_high_density_high_score(self, engine, complex_dish):
        """320 kcal/100g is above max threshold."""
        score = engine.caloric_density_score(complex_dish)
        assert score == 1.0

    def test_threshold_density(self, engine, edge_dish):
        """Exactly 150 kcal/100g is at threshold."""
        score = engine.caloric_density_score(edge_dish)
        assert score == 0.0

    def test_zero_mass_returns_middle(self, engine):
        """Zero mass should return middle score."""
        dish = NutritionDish(
            dish_id="zero",
            total_calories=100,
            total_mass=0,  # Invalid
            total_fat=0,
            total_carb=0,
            total_protein=0,
            ingredients=[],
            complexity="pending",
        )
        score = engine.caloric_density_score(dish)
        assert score == 0.5


class TestAmbiguityScore:
    """Tests for ingredient ambiguity scoring."""

    def test_distinct_names_low_score(self, engine, simple_dish):
        """Clear ingredient names should have low ambiguity."""
        score = engine.ambiguity_score(simple_dish)
        assert score == 0.0

    def test_sauce_increases_ambiguity(self, engine, complex_dish):
        """Sauce in ingredients increases ambiguity."""
        score = engine.ambiguity_score(complex_dish)
        assert score > 0.0

    def test_empty_ingredients_middle(self, engine):
        """Empty ingredients returns middle score."""
        dish = NutritionDish(
            dish_id="empty",
            total_calories=0,
            total_mass=0,
            total_fat=0,
            total_carb=0,
            total_protein=0,
            ingredients=[],
            complexity="pending",
        )
        score = engine.ambiguity_score(dish)
        assert score == 0.5


class TestStratificationScores:
    """Tests for weighted average calculation."""

    def test_weighted_average_all_zero(self):
        """All zero scores should yield zero weighted average."""
        scores = StratificationScores(
            ingredient_count=0.0,
            visual_distinctiveness=0.0,
            caloric_density=0.0,
            ambiguity=0.0,
        )
        assert scores.weighted_average == 0.0

    def test_weighted_average_all_one(self):
        """All one scores should yield one weighted average."""
        scores = StratificationScores(
            ingredient_count=1.0,
            visual_distinctiveness=1.0,
            caloric_density=1.0,
            ambiguity=1.0,
        )
        assert scores.weighted_average == 1.0

    def test_weighted_average_mixed(self):
        """Mixed scores should yield weighted average."""
        scores = StratificationScores(
            ingredient_count=0.5,
            visual_distinctiveness=0.5,
            caloric_density=0.5,
            ambiguity=0.5,
        )
        assert scores.weighted_average == 0.5


class TestClassify:
    """Tests for final classification."""

    def test_simple_dish_classified_simple(self, engine, simple_dish):
        """Simple dish should be classified as 'simple'."""
        result = engine.classify(simple_dish)
        assert result == "simple"

    def test_complex_dish_classified_complex(self, engine, complex_dish):
        """Complex dish should be classified as 'complex'."""
        result = engine.classify(complex_dish)
        assert result == "complex"

    def test_classification_returns_string(self, engine, edge_dish):
        """Classification should return string 'simple' or 'complex'."""
        result = engine.classify(edge_dish)
        assert result in ["simple", "complex"]

    def test_get_scores_returns_dataclass(self, engine, simple_dish):
        """get_scores should return StratificationScores dataclass."""
        scores = engine.get_scores(simple_dish)
        assert isinstance(scores, StratificationScores)
        assert hasattr(scores, "ingredient_count")
        assert hasattr(scores, "visual_distinctiveness")
        assert hasattr(scores, "caloric_density")
        assert hasattr(scores, "ambiguity")


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_dish_same_classification(self, engine, simple_dish):
        """Same dish should always get same classification."""
        results = [engine.classify(simple_dish) for _ in range(10)]
        assert all(r == results[0] for r in results)

    def test_same_dish_same_scores(self, engine, complex_dish):
        """Same dish should always get same scores."""
        scores1 = engine.get_scores(complex_dish)
        scores2 = engine.get_scores(complex_dish)
        assert scores1.weighted_average == scores2.weighted_average
