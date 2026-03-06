"""Tests for targeted clarification question generation based on dominant_factor."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.constants import CLARIFICATION_TEMPLATES
from app.schemas.analysis import FoodItem
from app.services.llm_service import ClarificationQuestion, generate_clarification_question


def _make_items():
    return [FoodItem(name="Mystery Meat", quantity="1", calories=300, confidence=0.5)]


@pytest.fixture
def mock_llm_provider():
    """Force the provider to 'openai' and mock the OpenAI client."""
    with patch("app.services.llm_service.settings") as mock_settings:
        mock_settings.LLM_PROVIDER = "openai"
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.OPENAI_MODEL_NAME = "gpt-4o"

        mock_client = AsyncMock()
        parsed_result = ClarificationQuestion(question="Q?", options=["A", "B"])
        mock_choice = MagicMock()
        mock_choice.message.parsed = parsed_result
        mock_client.beta.chat.completions.parse.return_value.choices = [mock_choice]

        with patch("app.services.llm_service._get_openai_client", return_value=mock_client):
            yield mock_client


@pytest.mark.asyncio
async def test_prep_factor_uses_prep_template(mock_llm_provider):
    """dominant_factor='prep' should inject the prep template into the system prompt."""
    await generate_clarification_question(_make_items(), language="en", dominant_factor="prep")

    call_args = mock_llm_provider.beta.chat.completions.parse.call_args
    messages = call_args.kwargs["messages"]
    system_prompt = messages[0]["content"]
    assert CLARIFICATION_TEMPLATES["prep"] in system_prompt


@pytest.mark.asyncio
async def test_volume_factor_uses_volume_template(mock_llm_provider):
    """dominant_factor='volume' should inject the volume template into the system prompt."""
    await generate_clarification_question(_make_items(), language="en", dominant_factor="volume")

    call_args = mock_llm_provider.beta.chat.completions.parse.call_args
    messages = call_args.kwargs["messages"]
    system_prompt = messages[0]["content"]
    assert CLARIFICATION_TEMPLATES["volume"] in system_prompt
    assert CLARIFICATION_TEMPLATES["prep"] not in system_prompt


@pytest.mark.asyncio
async def test_ingredients_factor_uses_ingredients_template(mock_llm_provider):
    """dominant_factor='ingredients' should inject the ingredients template."""
    await generate_clarification_question(_make_items(), language="en", dominant_factor="ingredients")

    call_args = mock_llm_provider.beta.chat.completions.parse.call_args
    messages = call_args.kwargs["messages"]
    system_prompt = messages[0]["content"]
    assert CLARIFICATION_TEMPLATES["ingredients"] in system_prompt


@pytest.mark.asyncio
async def test_none_factor_uses_default_template(mock_llm_provider):
    """dominant_factor=None should use the default template."""
    await generate_clarification_question(_make_items(), language="en", dominant_factor=None)

    call_args = mock_llm_provider.beta.chat.completions.parse.call_args
    messages = call_args.kwargs["messages"]
    system_prompt = messages[0]["content"]
    assert CLARIFICATION_TEMPLATES["default"] in system_prompt
