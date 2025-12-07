"""LLM analysis service using OpenAI GPT-4o."""
import logging
from datetime import datetime
from functools import lru_cache

from openai import AsyncOpenAI

from app.config import settings
from app.schemas.analysis import AnalysisResult

logger = logging.getLogger(__name__)


class LLMGenerationError(Exception):
    """Custom exception for LLM generation failures."""

    pass


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    """Lazily instantiate and cache the OpenAI client."""
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


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
