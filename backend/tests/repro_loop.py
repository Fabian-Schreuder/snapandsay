import asyncio
import json
import os
import sys

from google import genai

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.analysis import AnalysisResult
from app.services.llm_service import _clean_schema_for_google


async def repro():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Set GOOGLE_API_KEY")
        return

    client = genai.Client(api_key=api_key)
    model_id = "gemini-3-flash-preview"  # matching logs

    prompt = (
        "IMPORTANT: Respond entirely in Dutch.\n"
        "You are a dietary expert. Current time is 13:35. Analyze the input to identify food items, estimate quantities, calories, and confidence.\n"
        "Rate meal complexity from 0.0 (simple, single item) to 1.0 (complex, multi-component) considering: number of distinct items, composite dishes, ambiguous portions, mixed preparations.\n"
        "Assess ambiguity (0-3) for: Hidden Ingredients, Invisible Prep, Portion Ambiguity.\n"
        "Respond ONLY with valid JSON matching the configured response schema."
    )
    transcript = "Transcript: Moet ik iets zeggen nu? Ja. Nou, dit is gebraden kip met aardappelen, wortelen en spruitjes en zuur. En dan? Nog een keer omdat het klopt. Dat klopt. Ja. Deze hier."

    schema = _clean_schema_for_google(AnalysisResult.model_json_schema())
    print("Schema being used:")
    print(json.dumps(schema, indent=2))

    contents = [prompt, transcript]

    print("\nStarting generation...")
    accumulated = ""
    try:
        response_stream = await client.aio.models.generate_content_stream(
            model=model_id,
            contents=contents,
            config={
                "response_mime_type": "application/json",
                "response_schema": schema,
            },
        )

        async for chunk in response_stream:
            text = chunk.text
            accumulated += text
            print(f"Received chunk ({len(text)} chars). Total: {len(accumulated)}")
            if len(accumulated) > 10000:
                print("LOOP DETECTED! (Generated > 10000 chars for simple input)")
                break

        print("\nFinal Result:")
        print(accumulated[:500] + "...")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(repro())
