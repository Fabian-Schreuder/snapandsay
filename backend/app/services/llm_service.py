"""LLM analysis service using OpenAI GPT-4o."""

import json
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime
from functools import lru_cache

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import settings
from app.schemas.analysis import AnalysisResult, FoodItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMGenerationError(Exception):
    """Custom exception for LLM generation failures."""

    pass


class ClarificationQuestion(BaseModel):
    """Schema for generated clarification question."""

    question: str
    options: list[str]


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    """Lazily instantiate and cache the OpenAI client."""
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY, timeout=60.0, max_retries=3)


def _build_messages(image_url: str | None, transcript: str | None, context: str | None = None) -> list[dict]:
    """Build the message list for the LLM request."""
    current_time = datetime.now().strftime("%H:%M")
    system_prompt = (
        f"You are a dietary expert. The current time is {current_time}. "
        "Analyze the provided input (image and/or audio transcript) to identify food items, "
        "estimate quantities, calories, and provide a confidence score. "
        "Generate a short, descriptive title for the meal (e.g. 'Roasted Cashews', 'Chicken Salad'). "
        "Infer the meal type (Breakfast, Lunch, Dinner, Snack) based on time and content. "
        "If the image is unclear, does not contain food, or you cannot analyze it for any reason, "
        "do NOT refuse. Instead, return a valid JSON object with an empty 'items' list "
        "and a 'synthesis_comment' explaining the issue. "
        "Provide the output in JSON format complying with this schema: "
        f"{json.dumps(AnalysisResult.model_json_schema(), ensure_ascii=False)}"
    )

    messages = [{"role": "system", "content": system_prompt}]

    user_content = []
    if context:
        user_content.append({"type": "text", "text": f"Context/Clarification: {context}"})

    if transcript:
        user_content.append({"type": "text", "text": f"Audio Transcript: {transcript}"})

    if image_url:
        user_content.append({"type": "image_url", "image_url": {"url": image_url}})

    messages.append({"role": "user", "content": user_content})

    # Debug logging
    log_content = []
    for item in user_content:
        if item["type"] == "text":
            log_content.append(f"Text: {item['text'][:50]}...")
        elif item["type"] == "image_url":
            url = item["image_url"]["url"]
            log_content.append(f"Image: {url[:30]}... (len={len(url)})")
    logger.info(f"Constructed LLM messages: {log_content}")

    return messages


async def _get_image_content(image_path: str, token: str | None = None) -> str:
    """
    Get image content as base64 data URI.
    Handles private Supabase Storage paths by downloading with user token.
    """
    import base64

    import httpx

    # Return as-is if it's already a data URI
    if image_path.startswith("data:"):
        return image_path

    # If it's a URL, try to download and base64 encode it
    if image_path.startswith(("http://", "https://")):

        # Add authentication for Supabase authenticated storage
        if token and settings.SUPABASE_URL and "supabase" in image_path:
            # Basic check if it's the authenticated endpoint or just a public one?
            # For now, if token provided and 'supabase' in URL, try adding header.
            # Only if it looks like the authenticated path?
            # The existing code added header if 'authenticated' in path?
            # The existing code constructed the URL. Here we assume image_path IS the URL.
            # BUT wait, the existing code constructed the URL if it WAS NOT a URL.
            pass

        # If the path is ALREADY a full URL (which it is for GCS), we just download it.
        # If it is a Supabase path (not URL) handled below?
        # The existing code handled:
        # 1. External URL (returns as is)
        # 2. Supabase path (not URL) -> constructs URL and downloads.

        # We want to change #1 to Download.

        async with httpx.AsyncClient() as client:
            try:
                # Prepare headers if needed (for now, assume external URLs don't need auth,
                # or rely on Supabase logic below for internal paths)
                req_headers = {}
                if "supabase" in image_path and "/authenticated/" in image_path and token:
                    req_headers["Authorization"] = f"Bearer {token}"

                response = await client.get(
                    image_path, headers=req_headers, follow_redirects=True, timeout=30.0
                )
                if response.status_code == 200:
                    b64_image = base64.b64encode(response.content).decode("utf-8")
                    mime_type = "image/jpeg"
                    if image_path.lower().endswith(".png"):
                        mime_type = "image/png"
                    elif image_path.lower().endswith(".webp"):
                        mime_type = "image/webp"
                    return f"data:{mime_type};base64,{b64_image}"
                else:
                    logger.warning(f"Failed to download image from {image_path}: {response.status_code}")
                    # Fallback to returning URL if download fails (maybe OpenAI can access it?)
                    return image_path
            except Exception as e:
                logger.warning(f"Failed to download/encode image: {e}")
                return image_path

    # Handle internal Supabase paths (not starting with http)
    if token and settings.SUPABASE_URL and "supabase" not in image_path:
        # Construct authenticated storage URL
        url = f"{settings.SUPABASE_URL}/storage/v1/object/authenticated/raw_uploads/{image_path}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers={"Authorization": f"Bearer {token}"})

            if response.status_code == 200:
                b64_image = base64.b64encode(response.content).decode("utf-8")
                mime_type = "image/jpeg"
                if image_path.lower().endswith(".png"):
                    mime_type = "image/png"
                elif image_path.lower().endswith(".webp"):
                    mime_type = "image/webp"

                return f"data:{mime_type};base64,{b64_image}"
            else:
                logger.warning(f"Failed to download image from Supabase: {response.status_code}")
                logger.debug(f"Failed URL: {url}")

    # Fallback: return original path (likely to fail if private)
    return image_path or ""


async def analyze_multimodal(
    image_url: str | None = None,
    transcript: str | None = None,
    context: str | None = None,
    user_token: str | None = None,
) -> AnalysisResult:
    """
    Analyze image and/or transcript using GPT-4o to extract dietary data.

    Args:
        image_url: URL or path of the image to analyze (optional).
        transcript: Audio transcript to analyze (optional).
        context: Additional textual context (e.g. clarification response) (optional).
        user_token: User JWT for accessing private images (optional).

    Returns:
        AnalysisResult with identified food items and synthesis comment.

    Raises:
        ValueError: If neither image_url nor transcript is provided.
        LLMGenerationError: If the LLM API call fails.
    """
    if not image_url and not transcript:
        raise ValueError("No input provided (image_url or transcript required)")

    # Process image if provided
    final_image_url = image_url
    if image_url:
        final_image_url = await _get_image_content(image_url, user_token)

    messages = _build_messages(final_image_url, transcript, context)

    try:
        client = _get_client()
        completion = await client.beta.chat.completions.parse(
            model=settings.OPENAI_MODEL_NAME,
            messages=messages,
            response_format=AnalysisResult,
        )
        if completion.choices[0].message.refusal:
            raise LLMGenerationError(f"LLM Refusal: {completion.choices[0].message.refusal}")
        return completion.choices[0].message.parsed
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise LLMGenerationError(f"Failed to analyze input: {str(e)}") from e


async def analyze_multimodal_streaming(
    image_url: str | None = None,
    transcript: str | None = None,
    context: str | None = None,
    on_token: Callable[[str], Awaitable[None]] | None = None,
    user_token: str | None = None,
) -> AnalysisResult:
    """
    Analyze image and/or transcript using GPT-4o with streaming tokens.

    This method streams tokens as they are generated, calling on_token for each
    chunk to enable real-time progress feedback in the UI.

    Args:
        image_url: URL or path of the image to analyze (optional).
        transcript: Audio transcript to analyze (optional).
        context: Additional textual context (e.g. clarification response) (optional).
        on_token: Optional async callback invoked with each text chunk.
        user_token: User JWT for accessing private images (optional).

    Returns:
        AnalysisResult with identified food items and synthesis comment.

    Raises:
        ValueError: If neither image_url nor transcript is provided.
        LLMGenerationError: If the LLM API call fails.
    """
    if not image_url and not transcript:
        raise ValueError("No input provided (image_url or transcript required)")

    # Process image if provided
    final_image_url = image_url
    if image_url:
        final_image_url = await _get_image_content(image_url, user_token)

    messages = _build_messages(final_image_url, transcript, context)
    accumulated_content = ""
    accumulated_refusal = ""

    try:
        client = _get_client()

        # Use streaming mode
        logger.info(f"Sending messages to LLM: {messages}")
        stream = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=messages,
            stream=True,
            response_format={"type": "json_object"},
        )

        logger.info("Starting LLM stream iteration...")
        async for chunk in stream:
            if chunk.choices:
                # Log the entire chunk for debugging
                logger.info(f"Chunk received: {chunk}")
                delta = chunk.choices[0].delta
                if delta.content:
                    content = delta.content
                    accumulated_content += content
                    logger.info(f"Token received: {content!r}")

                    # Call the token callback if provided
                    if on_token:
                        await on_token(content)
                elif delta.refusal:
                    accumulated_refusal += delta.refusal
                    logger.warning(f"Refusal token received: {delta.refusal}")

            if chunk.choices[0].finish_reason:
                logger.info(f"LLM Stream Finished. Reason: {chunk.choices[0].finish_reason}")
                logger.info(f"Total accumulated content length: {len(accumulated_content)}")

        if accumulated_refusal:
            logger.error(f"LLM returned refusal: {accumulated_refusal}")
            raise LLMGenerationError(f"LLM Refused to process input: {accumulated_refusal}")

        if not accumulated_content:
            logger.error("LLM returned empty response. Accumulated content is empty.")
            # dump messages to see what we sent
            logger.error(f"Request messages were: {json.dumps(messages, default=str)}")
            raise LLMGenerationError("LLM returned empty response")

        logger.info(f"LLM Response Content (first 200 chars): {accumulated_content[:200]}")

        # Parse the accumulated JSON into AnalysisResult
        try:
            parsed_data = json.loads(accumulated_content)
            return AnalysisResult.model_validate(parsed_data)
        except (json.JSONDecodeError, Exception) as parse_error:
            logger.error(
                f"Failed to parse streaming response: {parse_error}. " f"Content: {accumulated_content}"
            )
            raise LLMGenerationError(f"Failed to parse LLM response: {str(parse_error)}") from parse_error

    except Exception as e:
        logger.error(f"LLM streaming generation failed: {e}")
        raise LLMGenerationError(f"Failed to analyze input: {str(e)}") from e


async def generate_clarification_question(
    low_confidence_items: list[FoodItem],
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
        f"- {item.name} ({item.quantity}, confidence: {item.confidence:.0%})" for item in low_confidence_items
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
