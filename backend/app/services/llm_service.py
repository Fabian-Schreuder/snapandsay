"""LLM analysis service using OpenAI GPT-4o."""
import json
import logging
from datetime import datetime
from functools import lru_cache
from typing import AsyncGenerator, Callable, Awaitable, List

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import settings
from app.schemas.analysis import AnalysisResult, FoodItem

logger = logging.getLogger(__name__)


class LLMGenerationError(Exception):
    """Custom exception for LLM generation failures."""

    pass


class ClarificationQuestion(BaseModel):
    """Schema for generated clarification question."""
    question: str
    options: List[str]


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    """Lazily instantiate and cache the OpenAI client."""
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def _build_messages(
    image_url: str | None, transcript: str | None
) -> list[dict]:
    """Build the message list for the LLM request."""
    current_time = datetime.now().strftime("%H:%M")
    system_prompt = (
        f"You are a dietary expert. The current time is {current_time}. "
        "Analyze the provided input (image and/or audio transcript) to identify food items, "
        "estimate quantities, calories, and provide a confidence score. "
        "Infer the meal type (Breakfast, Lunch, Dinner, Snack) based on time and content."
    )

    messages = [{"role": "system", "content": system_prompt}]

    user_content = []
    if transcript:
        user_content.append({"type": "text", "text": f"Audio Transcript: {transcript}"})

    if image_url:
        user_content.append({"type": "image_url", "image_url": {"url": image_url}})

    messages.append({"role": "user", "content": user_content})
    return messages


async def analyze_multimodal(
    image_url: str | None = None, transcript: str | None = None
) -> AnalysisResult:
    """
    Analyze image and/or transcript using GPT-4o to extract dietary data.

    Args:
        image_url: URL of the image to analyze (optional).
        transcript: Audio transcript to analyze (optional).

    Returns:
        AnalysisResult with identified food items and synthesis comment.

    Raises:
        ValueError: If neither image_url nor transcript is provided.
        LLMGenerationError: If the LLM API call fails.
    """
    if not image_url and not transcript:
        raise ValueError("No input provided (image_url or transcript required)")

    messages = _build_messages(image_url, transcript)

    try:
        client = _get_client()
        completion = await client.beta.chat.completions.parse(
            model=settings.OPENAI_MODEL_NAME,
            messages=messages,
            response_format=AnalysisResult,
        )
        return completion.choices[0].message.parsed
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise LLMGenerationError(f"Failed to analyze input: {str(e)}")


async def analyze_multimodal_streaming(
    image_url: str | None = None,
    transcript: str | None = None,
    on_token: Callable[[str], Awaitable[None]] | None = None,
) -> AnalysisResult:
    """
    Analyze image and/or transcript using GPT-4o with streaming tokens.

    This method streams tokens as they are generated, calling on_token for each
    chunk to enable real-time progress feedback in the UI.

    Args:
        image_url: URL of the image to analyze (optional).
        transcript: Audio transcript to analyze (optional).
        on_token: Optional async callback invoked with each text chunk.

    Returns:
        AnalysisResult with identified food items and synthesis comment.

    Raises:
        ValueError: If neither image_url nor transcript is provided.
        LLMGenerationError: If the LLM API call fails.
    """
    if not image_url and not transcript:
        raise ValueError("No input provided (image_url or transcript required)")

    messages = _build_messages(image_url, transcript)
    accumulated_content = ""

    try:
        client = _get_client()
        
        # Use streaming mode
        stream = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=messages,
            stream=True,
            response_format={"type": "json_object"},
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                accumulated_content += content
                
                # Call the token callback if provided
                if on_token:
                    await on_token(content)

        # Parse the accumulated JSON into AnalysisResult
        try:
            parsed_data = json.loads(accumulated_content)
            return AnalysisResult.model_validate(parsed_data)
        except (json.JSONDecodeError, Exception) as parse_error:
            logger.error(f"Failed to parse streaming response: {parse_error}")
            raise LLMGenerationError(f"Failed to parse LLM response: {str(parse_error)}")

    except Exception as e:
        logger.error(f"LLM streaming generation failed: {e}")
        raise LLMGenerationError(f"Failed to analyze input: {str(e)}")


async def generate_clarification_question(
    low_confidence_items: List[FoodItem],
) -> ClarificationQuestion:
    """
    Generate a clarification question for low-confidence food items.
    
    Uses GPT-4o to create a simple, senior-friendly question with 2-3
    suggested options based on the uncertain food items.
    
    Args:
        low_confidence_items: List of FoodItem with low confidence scores.
        
    Returns:
        ClarificationQuestion with question text and options.
        
    Raises:
        LLMGenerationError: If the LLM call fails.
    """
    if not low_confidence_items:
        return ClarificationQuestion(
            question="I'm not sure what you ate. Can you describe it?",
            options=["Breakfast", "Lunch", "Dinner"],
        )
    
    # Build item descriptions for the prompt
    item_descriptions = [
        f"- {item.name} ({item.quantity}, confidence: {item.confidence:.0%})"
        for item in low_confidence_items
    ]
    items_text = "\n".join(item_descriptions)
    
    system_prompt = (
        "You are a friendly dietary assistant helping seniors log their meals. "
        "Generate a single, simple clarification question about uncertain food items. "
        "Requirements:\n"
        "- Use 6th grade reading level\n"
        "- Keep the question under 15 words\n"
        "- Provide 2-3 common answer options\n"
        "- Be friendly and patient\n"
        "- Focus on the most uncertain item"
    )
    
    user_prompt = (
        f"The following food items have low confidence scores:\n{items_text}\n\n"
        "Generate a simple clarification question to help identify them better."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    try:
        client = _get_client()
        completion = await client.beta.chat.completions.parse(
            model=settings.OPENAI_MODEL_NAME,
            messages=messages,
            response_format=ClarificationQuestion,
        )
        return completion.choices[0].message.parsed
    except Exception as e:
        logger.error(f"Clarification generation failed: {e}")
        # Fallback to generic question
        return ClarificationQuestion(
            question="Can you tell me more about what you ate?",
            options=["Main dish", "Side dish", "Drink"],
        )


