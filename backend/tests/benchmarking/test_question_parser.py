"""
Unit tests for Question Parser.
"""

import pytest

from app.benchmarking.question_parser import QuestionParser, QuestionType
from app.benchmarking.schemas import IngredientInfo, NutritionDish


@pytest.fixture
def parser():
    return QuestionParser()


@pytest.fixture
def sample_dish():
    """Sample dish with various ingredients for testing answer generation."""
    return NutritionDish(
        dish_id="test_001",
        total_calories=450,
        total_mass=350,
        total_fat=20,
        total_carb=45,
        total_protein=25,
        ingredients=[
            IngredientInfo(id="1", name="grilled chicken", grams=150),
            IngredientInfo(id="2", name="olive oil", grams=15),
            IngredientInfo(id="3", name="caesar dressing", grams=30),
            IngredientInfo(id="4", name="romaine lettuce", grams=100),
            IngredientInfo(id="5", name="parmesan cheese", grams=20),
        ],
        complexity="complex",
    )


class TestQuestionParsing:
    """Tests for question intent detection."""

    def test_parse_fat_question_explicit(self, parser):
        """Should detect fat/oil questions."""
        intent = parser.parse("What oil did you use for cooking?")
        assert intent.question_type == QuestionType.FAT_TYPE

    def test_parse_fat_question_butter(self, parser):
        """Should detect butter questions as fat type."""
        intent = parser.parse("Did you add any butter?")
        assert intent.question_type == QuestionType.FAT_TYPE

    def test_parse_quantity_how_much(self, parser):
        """Should detect 'how much' quantity questions."""
        intent = parser.parse("How much chicken did you have?")
        assert intent.question_type == QuestionType.QUANTITY
        assert intent.entity is not None

    def test_parse_quantity_how_many(self, parser):
        """Should detect 'how many' quantity questions."""
        intent = parser.parse("How many eggs did you eat?")
        assert intent.question_type == QuestionType.QUANTITY

    def test_parse_type_question(self, parser):
        """Should detect 'what type' questions."""
        intent = parser.parse("What type of bread was it?")
        assert intent.question_type == QuestionType.INGREDIENT_TYPE

    def test_parse_kind_question(self, parser):
        """Should detect 'what kind' questions."""
        intent = parser.parse("What kind of cheese was used?")
        assert intent.question_type == QuestionType.INGREDIENT_TYPE

    def test_parse_dressing_question(self, parser):
        """Should detect dressing/sauce questions."""
        intent = parser.parse("Was there any dressing on the salad?")
        assert intent.question_type == QuestionType.DRESSING_SAUCE

    def test_parse_sauce_question(self, parser):
        """Should detect sauce questions."""
        intent = parser.parse("Did you add any sauce?")
        assert intent.question_type == QuestionType.DRESSING_SAUCE

    def test_parse_cooking_method(self, parser):
        """Should detect cooking method questions."""
        intent = parser.parse("How was the chicken cooked?")
        assert intent.question_type == QuestionType.COOKING_METHOD

    def test_parse_cooking_method_fried(self, parser):
        """Should detect fried cooking method."""
        intent = parser.parse("Was it fried or baked?")
        assert intent.question_type == QuestionType.COOKING_METHOD

    def test_parse_portion_size(self, parser):
        """Should detect portion size questions."""
        intent = parser.parse("What was the portion size?")
        assert intent.question_type == QuestionType.PORTION_SIZE

    def test_parse_serving_question(self, parser):
        """Should detect serving questions as portion size."""
        intent = parser.parse("How big was the serving?")
        assert intent.question_type == QuestionType.PORTION_SIZE

    def test_parse_unknown_fallback(self, parser):
        """Unrecognized questions should fall back to UNKNOWN."""
        intent = parser.parse("What color was the tablecloth?")
        assert intent.question_type == QuestionType.UNKNOWN

    def test_parse_preserves_original_question(self, parser):
        """Should preserve original question in intent."""
        question = "How much rice did you eat?"
        intent = parser.parse(question)
        assert intent.original_question == question


class TestAnswerGeneration:
    """Tests for answer generation based on dish metadata."""

    def test_answer_fat_type_found(self, parser, sample_dish):
        """Should find and report olive oil."""
        intent = parser.parse("What oil did you use?")
        answer = parser.lookup_answer(intent, sample_dish)
        assert "olive oil" in answer.lower()
        assert "15" in answer  # grams

    def test_answer_fat_type_not_found(self, parser):
        """Should report no fat when none present."""
        dish = NutritionDish(
            dish_id="no_fat",
            total_calories=100,
            total_mass=200,
            total_fat=0,
            total_carb=20,
            total_protein=5,
            ingredients=[
                IngredientInfo(id="1", name="apple", grams=150),
            ],
            complexity="simple",
        )
        intent = parser.parse("Did you use any oil?")
        answer = parser.lookup_answer(intent, dish)
        assert "no" in answer.lower() or "not" in answer.lower()

    def test_answer_quantity_specific(self, parser, sample_dish):
        """Should report quantity for specific ingredient."""
        intent = parser.parse("How much chicken did you have?")
        answer = parser.lookup_answer(intent, sample_dish)
        assert "150" in answer or "chicken" in answer.lower()

    def test_answer_quantity_not_found(self, parser, sample_dish):
        """Should report ingredient not found."""
        intent = parser.parse("How much rice did you have?")
        answer = parser.lookup_answer(intent, sample_dish)
        assert "rice" in answer.lower() or "don't see" in answer.lower()

    def test_answer_dressing_found(self, parser, sample_dish):
        """Should find caesar dressing."""
        intent = parser.parse("Any dressing?")
        answer = parser.lookup_answer(intent, sample_dish)
        assert "caesar" in answer.lower() or "dressing" in answer.lower()

    def test_answer_dressing_not_found(self, parser):
        """Should report no dressing when none present."""
        dish = NutritionDish(
            dish_id="no_dressing",
            total_calories=200,
            total_mass=250,
            total_fat=5,
            total_carb=30,
            total_protein=15,
            ingredients=[
                IngredientInfo(id="1", name="chicken breast", grams=150),
                IngredientInfo(id="2", name="steamed broccoli", grams=100),
            ],
            complexity="simple",
        )
        intent = parser.parse("Was there any dressing?")
        answer = parser.lookup_answer(intent, dish)
        assert "no" in answer.lower()

    def test_answer_portion_size(self, parser, sample_dish):
        """Should report total portion size."""
        intent = parser.parse("What was the portion size?")
        answer = parser.lookup_answer(intent, sample_dish)
        assert "350" in answer  # total_mass

    def test_answer_cooking_method_inferred(self, parser, sample_dish):
        """Should infer cooking method from ingredient names."""
        intent = parser.parse("How was it cooked?")
        answer = parser.lookup_answer(intent, sample_dish)
        assert "grilled" in answer.lower() or "not sure" in answer.lower()

    def test_answer_unknown_returns_summary(self, parser, sample_dish):
        """Unknown questions should return full summary."""
        intent = parser.parse("What is the meaning of life?")
        answer = parser.lookup_answer(intent, sample_dish)
        # Summary contains ingredient list and macros
        assert "kcal" in answer or "contains" in answer.lower()


class TestIngredientType:
    """Tests for ingredient type questions."""

    def test_answer_ingredient_type_found(self, parser, sample_dish):
        """Should identify specific ingredient type."""
        intent = parser.parse("What type of cheese was it?")
        answer = parser.lookup_answer(intent, sample_dish)
        assert "parmesan" in answer.lower()

    def test_answer_ingredient_type_not_found(self, parser, sample_dish):
        """Should report when ingredient type not found."""
        intent = parser.parse("What type of rice was it?")
        answer = parser.lookup_answer(intent, sample_dish)
        assert "rice" in answer.lower()


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_question(self, parser):
        """Empty question should return UNKNOWN."""
        intent = parser.parse("")
        assert intent.question_type == QuestionType.UNKNOWN

    def test_empty_ingredients_fat(self, parser):
        """Should handle dish with no ingredients for fat query."""
        dish = NutritionDish(
            dish_id="empty",
            total_calories=0,
            total_mass=0,
            total_fat=0,
            total_carb=0,
            total_protein=0,
            ingredients=[],
            complexity="simple",
        )
        intent = parser.parse("What oil did you use?")
        answer = parser.lookup_answer(intent, dish)
        assert "no" in answer.lower()

    def test_case_insensitive_parsing(self, parser):
        """Parsing should be case insensitive."""
        intent1 = parser.parse("WHAT OIL DID YOU USE?")
        intent2 = parser.parse("what oil did you use?")
        assert intent1.question_type == intent2.question_type

    def test_special_characters_in_question(self, parser):
        """Should handle questions with special characters."""
        intent = parser.parse("How much chicken? (approximately)")
        assert intent.question_type == QuestionType.QUANTITY
