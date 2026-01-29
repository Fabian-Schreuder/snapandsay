"""
Question Parser for Oracle Benchmarking.

Parses agent clarification questions and returns targeted answers
based on Nutrition5k ground truth metadata.
"""

import re
from dataclasses import dataclass
from enum import Enum, auto

from app.benchmarking.schemas import NutritionDish


class QuestionType(Enum):
    """Types of clarification questions the agent may ask."""

    FAT_TYPE = auto()  # "What oil/fat was used?"
    QUANTITY = auto()  # "How much {ingredient}?"
    INGREDIENT_TYPE = auto()  # "What type of {category}?"
    DRESSING_SAUCE = auto()  # "Any dressing or sauce?"
    COOKING_METHOD = auto()  # "How was it cooked?"
    PORTION_SIZE = auto()  # "What was the portion size?"
    UNKNOWN = auto()  # Fallback


@dataclass
class QuestionIntent:
    """Parsed intent from a clarification question."""

    question_type: QuestionType
    entity: str | None = None  # Referenced ingredient or category
    original_question: str = ""


# Regex patterns for question classification
QUESTION_PATTERNS: list[tuple[re.Pattern, QuestionType, int | None]] = [
    # Fat/oil questions - check for standalone keywords first
    (re.compile(r"\b(oil|fat|butter|margarine)\b", re.I), QuestionType.FAT_TYPE, None),
    # Quantity questions - capture the key noun (typically last significant word)
    (re.compile(r"\bhow\s+much\s+(?:\w+\s+)*?(\w+)\s*(?:did|do|have|eat|use)?", re.I), QuestionType.QUANTITY, 1),  # noqa: E501
    (re.compile(r"\bquantity\b.*?\b(\w+)\b", re.I), QuestionType.QUANTITY, 1),
    (re.compile(r"\bhow\s+many\s+(?:\w+\s+)*?(\w+)", re.I), QuestionType.QUANTITY, 1),
    # Type questions - capture the noun being asked about
    (re.compile(r"\bwhat\s+type\s+of\s+(\w+)", re.I), QuestionType.INGREDIENT_TYPE, 1),
    (re.compile(r"\bwhat\s+kind\s+of\s+(\w+)", re.I), QuestionType.INGREDIENT_TYPE, 1),
    (re.compile(r"\bwhich\s+type\s+of\s+(\w+)", re.I), QuestionType.INGREDIENT_TYPE, 1),
    # Dressing/sauce questions
    (re.compile(r"\b(dressing|sauce|gravy|condiment)\b", re.I), QuestionType.DRESSING_SAUCE, None),
    (re.compile(r"\bany\b.*\b(topping|spread)\b", re.I), QuestionType.DRESSING_SAUCE, None),
    # Cooking method - check for the verb pattern "was ... cooked" or keywords
    (re.compile(r"\bhow\s+was\b.*\b(cook|cooked|prepare|prepared|made)\b", re.I), QuestionType.COOKING_METHOD, None),  # noqa: E501
    (re.compile(r"\bhow\b.*\b(cook|cooked|prepare|prepared|made)\b", re.I), QuestionType.COOKING_METHOD, None),  # noqa: E501
    (re.compile(r"\b(fried|baked|grilled|steamed|boiled|roasted)\b", re.I), QuestionType.COOKING_METHOD, None),  # noqa: E501
    # Portion size
    (re.compile(r"\b(portion|serving|size)\b", re.I), QuestionType.PORTION_SIZE, None),
]

# Ingredient category keywords for targeted lookups
FAT_KEYWORDS = frozenset({"oil", "butter", "margarine", "lard", "ghee", "shortening", "fat"})
SAUCE_KEYWORDS = frozenset(
    {"sauce", "dressing", "gravy", "ketchup", "mayo", "mayonnaise", "mustard", "vinaigrette"}
)


class QuestionParser:
    """
    Parses agent clarification questions and generates targeted Oracle responses.

    Instead of always returning the full dish summary, this parser identifies
    what specific information the agent is asking for and returns a focused answer.
    """

    def parse(self, question: str) -> QuestionIntent:
        """
        Parse a clarification question to determine intent and extract entities.
        """
        for pattern, q_type, entity_group in QUESTION_PATTERNS:
            match = pattern.search(question)
            if match:
                entity = None
                if entity_group is not None and len(match.groups()) >= entity_group:
                    entity = match.group(entity_group)
                return QuestionIntent(
                    question_type=q_type,
                    entity=entity,
                    original_question=question,
                )

        # Fallback to unknown
        return QuestionIntent(
            question_type=QuestionType.UNKNOWN,
            original_question=question,
        )

    def lookup_answer(self, intent: QuestionIntent, dish: NutritionDish) -> str:
        """
        Generate a targeted answer based on the question intent and dish metadata.
        """
        if intent.question_type == QuestionType.FAT_TYPE:
            return self._answer_fat_type(dish)

        elif intent.question_type == QuestionType.QUANTITY:
            return self._answer_quantity(dish, intent.entity)

        elif intent.question_type == QuestionType.INGREDIENT_TYPE:
            return self._answer_ingredient_type(dish, intent.entity)

        elif intent.question_type == QuestionType.DRESSING_SAUCE:
            return self._answer_dressing_sauce(dish)

        elif intent.question_type == QuestionType.COOKING_METHOD:
            return self._answer_cooking_method(dish)

        elif intent.question_type == QuestionType.PORTION_SIZE:
            return self._answer_portion_size(dish)

        else:
            # Fallback to full summary
            return dish.summary

    def _answer_fat_type(self, dish: NutritionDish) -> str:
        """Find and report any fat/oil ingredients."""
        fats = []
        for ing in dish.ingredients:
            name_lower = ing.name.lower()
            if any(kw in name_lower for kw in FAT_KEYWORDS):
                fats.append(f"{ing.grams:.1f}g {ing.name}")

        if fats:
            return f"I used {', '.join(fats)}."
        else:
            return "No added oil or fat that I can see."

    def _answer_quantity(self, dish: NutritionDish, entity: str | None) -> str:
        """Find quantity of a specific ingredient or report all quantities."""
        if entity:
            entity_lower = entity.lower()
            for ing in dish.ingredients:
                if entity_lower in ing.name.lower():
                    return f"About {ing.grams:.1f}g of {ing.name}."

            return f"I don't see {entity} in this dish."

        # If no specific entity, list all ingredients with quantities
        items = [f"{ing.grams:.1f}g {ing.name}" for ing in dish.ingredients]
        return f"The dish contains: {', '.join(items)}."

    def _answer_ingredient_type(self, dish: NutritionDish, entity: str | None) -> str:
        """Provide specific ingredient type information."""
        if entity:
            entity_lower = entity.lower()
            for ing in dish.ingredients:
                if entity_lower in ing.name.lower():
                    return f"It's {ing.name}."

            return f"I don't see {entity} specifically."

        # List all ingredient names
        names = [ing.name for ing in dish.ingredients]
        return f"The ingredients are: {', '.join(names)}."

    def _answer_dressing_sauce(self, dish: NutritionDish) -> str:
        """Report any dressings or sauces in the dish."""
        sauces = []
        for ing in dish.ingredients:
            name_lower = ing.name.lower()
            if any(kw in name_lower for kw in SAUCE_KEYWORDS):
                sauces.append(f"{ing.grams:.1f}g {ing.name}")

        if sauces:
            return f"Yes, there is {', '.join(sauces)}."
        else:
            return "No dressing or sauce."

    def _answer_cooking_method(self, dish: NutritionDish) -> str:
        """
        Infer cooking method from ingredient names.
        Note: Nutrition5k doesn't directly store cooking method, so we use heuristics.
        """
        all_names = " ".join(ing.name.lower() for ing in dish.ingredients)

        if "fried" in all_names or "fry" in all_names:
            return "It was fried."
        elif "baked" in all_names or "roasted" in all_names:
            return "It was baked or roasted."
        elif "grilled" in all_names:
            return "It was grilled."
        elif "steamed" in all_names:
            return "It was steamed."
        elif "boiled" in all_names:
            return "It was boiled."
        else:
            return "I'm not sure about the cooking method."

    def _answer_portion_size(self, dish: NutritionDish) -> str:
        """Report total portion size."""
        return f"The total portion size is {dish.total_mass:.1f}g."
