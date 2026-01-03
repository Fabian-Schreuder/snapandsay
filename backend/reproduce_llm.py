import asyncio
import logging

from app.config import settings
from app.services.llm_service import analyze_multimodal_streaming

# Configure logging to show our debug messages
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_llm_streaming():
    print(f"Testing LLM streaming with model: {settings.OPENAI_MODEL_NAME}")
    
    # Mock data
    transcript = "I had a bowl of oatmeal with blueberries and a coffee."
    
    print("\n--- Starting Stream ---")
    try:
        async def on_token(token):
            print(token, end="", flush=True)

        result = await analyze_multimodal_streaming(
            transcript=transcript,
            on_token=on_token
        )
        print("\n\n--- Stream Complete ---")
        print(f"Result: {result}")
    except Exception as e:
        print(f"\n\nERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_streaming())
