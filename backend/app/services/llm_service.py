"""LLM analysis service using OpenAI GPT-4o."""

import json
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime
from functools import lru_cache

from google import genai
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
def _get_openai_client() -> AsyncOpenAI:
    """Lazily instantiate and cache the OpenAI client."""
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY, timeout=60.0, max_retries=3)


@lru_cache(maxsize=1)
def _get_google_client() -> genai.Client:
    """Lazily instantiate and cache the Google GenAI client."""
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set in configuration")
    return genai.Client(api_key=settings.GOOGLE_API_KEY)


def _build_messages(
    image_url: str | None,
    transcript: str | None,
    context: str | None = None,
    language: str = "nl",
    system_prompt_override: str | None = None,
) -> list[dict]:
    """Build the message list for the LLM request."""
    current_time = datetime.now().strftime("%H:%M")
    lang_name = "Dutch" if language == "nl" else "English"
    lang_instruction = f"IMPORTANT: Respond entirely in {lang_name}. " if language != "en" else ""

    if system_prompt_override:
        # Use provided override, injecting standard parameters if they exist in template
        # Need to handle {current_time}, {schema}, {lang_instruction} if present
        schema_json = json.dumps(AnalysisResult.model_json_schema(), ensure_ascii=False)
        try:
            system_prompt = system_prompt_override.format(
                current_time=current_time, schema=schema_json, lang_instruction=lang_instruction
            )
        except (KeyError, ValueError):
            # If standard formatting fails, just use the string as is
            system_prompt = system_prompt_override
    else:
        system_prompt = (
            f"{lang_instruction}"
            f"You are a dietary expert. The current time is {current_time}. "
            "Analyze the provided input (image and/or audio transcript) to identify food items, "
            "estimate quantities, calories, and provide a confidence score.\n\n"
            "CRITICAL ESTIMATION RULES:\n"
            "1. First estimate the WEIGHT in grams by comparing to standard references:\n"
            "   - Dinner plate ~25cm, food portion often 150-300g\n"
            "   - Palm-sized portion ~100g\n"
            "2. Apply correct CALORIC DENSITY:\n"
            "   - Sausage/processed meat: 250-350 kcal/100g (HIGH FAT)\n"
            "   - Red meat (beef, pork): 200-250 kcal/100g\n"
            "   - Chicken breast: 165 kcal/100g\n"
            "   - Eggs: 155 kcal/100g (~70 kcal per egg)\n"
            "   - Rice/pasta cooked: 130 kcal/100g\n"
            "   - Vegetables: 25-50 kcal/100g\n"
            "   - Fruit: 40-60 kcal/100g\n"
            "3. When uncertain, estimate HIGHER rather than lower.\n\n"
            "Generate a short, descriptive title for the meal (e.g. 'Roasted Cashews', 'Chicken Salad'). "
            "Infer the meal type (Breakfast, Lunch, Dinner, Snack) based on time and content.\n\n"
            "VALIDATION RULES:\n"
            "- If the input contains food, drink, or supplements (vitamins, etc), set 'is_food' to true.\n"
            "- If the input is CLEARLY NOT food (e.g. shoes, car, furniture, pets), "
            "set 'is_food' to false and provide a 'non_food_reason'.\n"
            "- If the input is AMBIGUOUS, BLURRY, or UNCLEAR, set 'is_food' to true "
            "so we can ask for clarification (do not reject).\n"
            "- If you cannot analyze it, return a valid JSON with empty items and an explanation.\n\n"
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
    language: str = "nl",
    system_prompt_override: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> AnalysisResult:
    """
    Analyze image and/or transcript to extract dietary data.
    Supports OpenAI and Google Gemini providers.
    """
    if not image_url and not transcript:
        raise ValueError("No input provided (image_url or transcript required)")

    provider = provider or settings.LLM_PROVIDER

    # Process image if provided
    final_image_url = image_url
    if image_url:
        final_image_url = await _get_image_content(image_url, user_token)

    if provider == "google":
        return await _analyze_google(
            final_image_url, transcript, context, language, system_prompt_override, model
        )

    # Default to OpenAI
    messages = _build_messages(final_image_url, transcript, context, language, system_prompt_override)
    try:
        client = _get_openai_client()
        model_name = model or settings.OPENAI_MODEL_NAME
        completion = await client.beta.chat.completions.parse(
            model=model_name,
            messages=messages,
            response_format=AnalysisResult,
        )
        if completion.choices[0].message.refusal:
            raise LLMGenerationError(f"LLM Refusal: {completion.choices[0].message.refusal}")
        return completion.choices[0].message.parsed
    except Exception as e:
        logger.error(f"OpenAI analysis failed: {e}")
        raise LLMGenerationError(f"Failed to analyze input with OpenAI: {str(e)}") from e


async def _analyze_google(
    image_data_uri: str | None,
    transcript: str | None,
    context: str | None,
    language: str,
    system_prompt_override: str | None,
    model_name: str | None,
) -> AnalysisResult:
    """Inner helper for Google Gemini analysis."""
    client = _get_google_client()
    model_id = model_name or settings.GOOGLE_MODEL_NAME

    # Build prompt and parts
    current_time = datetime.now().strftime("%H:%M")
    lang_name = "Dutch" if language == "nl" else "English"
    lang_instruction = f"IMPORTANT: Respond entirely in {lang_name}." if language != "en" else ""

    schema_json = json.dumps(AnalysisResult.model_json_schema(), ensure_ascii=False)

    if system_prompt_override:
        try:
            prompt = system_prompt_override.format(
                current_time=current_time, schema=schema_json, lang_instruction=lang_instruction
            )
        except (KeyError, ValueError):
            prompt = system_prompt_override
    else:
        # Simplified version of the OpenAI prompt for Gemini
        prompt = (
            f"{lang_instruction}\n"
            f"You are a dietary expert. Current time is {current_time}. "
            "Analyze the input to identify food items, estimate quantities, calories, and confidence.\n"
            "Respond ONLY with valid JSON matching this schema: " + schema_json
        )

    contents = []
    if prompt:
        contents.append(prompt)
    if context:
        contents.append(f"Context: {context}")
    if transcript:
        contents.append(f"Transcript: {transcript}")

    if image_data_uri:
        if image_data_uri.startswith("data:"):
            import base64

            header, encoded = image_data_uri.split(",", 1)
            mime_type = header.split(";")[0].split(":")[1]
            image_bytes = base64.b64decode(encoded)
            contents.append({"mime_type": mime_type, "data": image_bytes})
        else:
            # If it's still a URL (fallback), Gemini might not support it directly in prompt parts easily
            # But the service usually ensures it's a data URI.
            pass

    try:
        response = await client.aio.models.generate_content(
            model=model_id,
            contents=contents,
            config={
                "response_mime_type": "application/json",
                "response_schema": AnalysisResult,
            },
        )
        return AnalysisResult.model_validate_json(response.text)
    except Exception as e:
        logger.error(f"Google analysis failed: {e}")
        raise LLMGenerationError(f"Failed to analyze input with Google: {str(e)}") from e


async def analyze_multimodal_streaming(
    image_url: str | None = None,
    transcript: str | None = None,
    context: str | None = None,
    on_token: Callable[[str], Awaitable[None]] | None = None,
    user_token: str | None = None,
    language: str = "nl",
    system_prompt_override: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> AnalysisResult:
    """
    Analyze image and/or transcript with streaming tokens.
    Supports OpenAI and Google Gemini providers.
    """
    if not image_url and not transcript:
        raise ValueError("No input provided (image_url or transcript required)")

    provider = provider or settings.LLM_PROVIDER

    # Process image if provided
    final_image_url = image_url
    if image_url:
        final_image_url = await _get_image_content(image_url, user_token)

    if provider == "google":
        return await _analyze_google_streaming(
            final_image_url, transcript, context, on_token, language, system_prompt_override, model
        )

    # Default to OpenAI
    messages = _build_messages(final_image_url, transcript, context, language, system_prompt_override)
    accumulated_content = ""
    accumulated_refusal = ""

    try:
        client = _get_openai_client()
        model_name = model or settings.OPENAI_MODEL_NAME

        # Use streaming mode
        logger.info(f"Sending messages to OpenAI: {messages}")
        stream = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=True,
            response_format={"type": "json_object"},
        )

        logger.info("Starting OpenAI stream iteration...")
        async for chunk in stream:
            if chunk.choices:
                # Log the entire chunk for debugging
                logger.debug(f"Chunk received: {chunk}")
                delta = chunk.choices[0].delta
                if delta.content:
                    content = delta.content
                    accumulated_content += content
                    # Call the token callback if provided
                    if on_token:
                        await on_token(content)
                elif delta.refusal:
                    accumulated_refusal += delta.refusal
                    logger.warning(f"Refusal token received: {delta.refusal}")

            if chunk.choices[0].finish_reason:
                logger.info(f"OpenAI Stream Finished. Reason: {chunk.choices[0].finish_reason}")

        if accumulated_refusal:
            logger.error(f"OpenAI returned refusal: {accumulated_refusal}")
            raise LLMGenerationError(f"OpenAI Refused to process input: {accumulated_refusal}")

        if not accumulated_content:
            logger.error("OpenAI returned empty response.")
            raise LLMGenerationError("OpenAI returned empty response")

        # Parse the accumulated JSON into AnalysisResult
        try:
            parsed_data = json.loads(accumulated_content)
            return AnalysisResult.model_validate(parsed_data)
        except (json.JSONDecodeError, Exception) as parse_error:
            logger.error(f"Failed to parse OpenAI response: {parse_error}")
            raise LLMGenerationError(f"Failed to parse OpenAI response: {str(parse_error)}") from parse_error

    except Exception as e:
        logger.error(f"LLM streaming generation failed: {e}")
        raise LLMGenerationError(f"Failed to analyze input: {str(e)}") from e


async def _analyze_google_streaming(
    image_data_uri: str | None,
    transcript: str | None,
    context: str | None,
    on_token: Callable[[str], Awaitable[None]] | None,
    language: str,
    system_prompt_override: str | None,
    model_name: str | None,
) -> AnalysisResult:
    """Inner helper for Google Gemini streaming analysis."""
    client = _get_google_client()
    model_id = model_name or settings.GOOGLE_MODEL_NAME

    # Build prompt and parts (reusing logic from _analyze_google)
    current_time = datetime.now().strftime("%H:%M")
    lang_name = "Dutch" if language == "nl" else "English"
    lang_instruction = f"IMPORTANT: Respond entirely in {lang_name}." if language != "en" else ""
    schema_json = json.dumps(AnalysisResult.model_json_schema(), ensure_ascii=False)

    if system_prompt_override:
        try:
            prompt = system_prompt_override.format(
                current_time=current_time, schema=schema_json, lang_instruction=lang_instruction
            )
        except (KeyError, ValueError):
            prompt = system_prompt_override
    else:
        prompt = (
            f"{lang_instruction}\n"
            f"You are a dietary expert. Current time is {current_time}. "
            "Analyze the input to identify food items, estimate quantities, calories, and confidence.\n"
            "Respond ONLY with valid JSON matching this schema: " + schema_json
        )

    contents = []
    if prompt:
        contents.append(prompt)
    if context:
        contents.append(f"Context: {context}")
    if transcript:
        contents.append(f"Transcript: {transcript}")

    if image_data_uri:
        if image_data_uri.startswith("data:"):
            import base64

            header, encoded = image_data_uri.split(",", 1)
            mime_type = header.split(";")[0].split(":")[1]
            image_bytes = base64.b64decode(encoded)
            contents.append({"mime_type": mime_type, "data": image_bytes})

    accumulated_content = ""
    try:
        response_stream = await client.aio.models.generate_content_stream(
            model=model_id,
            contents=contents,
            config={
                "response_mime_type": "application/json",
            },
        )

        async for chunk in response_stream:
            text = chunk.text
            accumulated_content += text
            if on_token:
                await on_token(text)

        return AnalysisResult.model_validate_json(accumulated_content)
    except Exception as e:
        logger.error(f"Google streaming analysis failed: {e}")
        raise LLMGenerationError(f"Failed to analyze input with Google (streaming): {str(e)}") from e


async def generate_clarification_question(
    low_confidence_items: list[FoodItem],
    language: str = "nl",
    provider: str | None = None,
    model: str | None = None,
) -> ClarificationQuestion:
    """
    Generate a clarification question for low-confidence food items.
    Supports OpenAI and Google Gemini providers.
    """
    provider = provider or settings.LLM_PROVIDER

    # Localized fallback messages
    fallback_messages = {
        "nl": {
            "empty_question": "Ik weet niet zeker wat u at. Kunt u het beschrijven?",
            "empty_options": ["Ontbijt", "Lunch", "Diner"],
            "generic_question": "Kunt u mij meer vertellen over wat u at?",
            "generic_options": ["Hoofdgerecht", "Bijgerecht", "Drank"],
        },
        "en": {
            "empty_question": "I'm not sure what you ate. Can you describe it?",
            "empty_options": ["Breakfast", "Lunch", "Dinner"],
            "generic_question": "Can you tell me more about what you ate?",
            "generic_options": ["Main dish", "Side dish", "Drink"],
        },
    }
    msgs = fallback_messages.get(language, fallback_messages["nl"])

    if not low_confidence_items:
        return ClarificationQuestion(
            question=msgs["empty_question"],
            options=msgs["empty_options"],
        )

    # Build item descriptions for the prompt
    item_descriptions = [
        f"- {item.name} ({item.quantity}, confidence: {item.confidence:.0%})" for item in low_confidence_items
    ]
    items_text = "\n".join(item_descriptions)

    lang_name = "Dutch" if language == "nl" else "English"
    lang_instruction = f"IMPORTANT: Respond entirely in {lang_name}. " if language != "en" else ""

    system_prompt = (
        f"{lang_instruction}"
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

    if provider == "google":
        return await _generate_google_clarification(system_prompt, user_prompt, language, model)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        client = _get_openai_client()
        model_name = model or settings.OPENAI_MODEL_NAME
        completion = await client.beta.chat.completions.parse(
            model=model_name,
            messages=messages,
            response_format=ClarificationQuestion,
        )
        return completion.choices[0].message.parsed
    except Exception as e:
        logger.error(f"OpenAI clarification generation failed: {e}")
        return ClarificationQuestion(
            question=msgs["generic_question"],
            options=msgs["generic_options"],
        )


async def _generate_google_clarification(
    system_prompt: str,
    user_prompt: str,
    language: str,
    model_name: str | None,
) -> ClarificationQuestion:
    """Inner helper for Google Gemini clarification generation."""
    client = _get_google_client()
    model_id = model_name or settings.GOOGLE_MODEL_NAME

    try:
        response = await client.aio.models.generate_content(
            model=model_id,
            contents=[system_prompt, user_prompt],
            config={
                "response_mime_type": "application/json",
                "response_schema": ClarificationQuestion,
            },
        )
        return ClarificationQuestion.model_validate_json(response.text)
    except Exception as e:
        logger.error(f"Google clarification generation failed: {e}")
        return ClarificationQuestion(
            question="Can you tell me more about what you ate?",
            options=["Main dish", "Side dish", "Drink"],
        )
