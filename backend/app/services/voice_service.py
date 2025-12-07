"""Voice transcription service using OpenAI Whisper."""
import asyncio
from functools import lru_cache
from openai import AsyncOpenAI
from app.config import settings


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    """Lazily instantiate and cache the OpenAI client."""
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def transcribe_audio(file_path: str) -> str:
    """
    Transcribe an audio file using OpenAI Whisper.

    Args:
        file_path: Path to the audio file.

    Returns:
        The transcribed text.

    Raises:
        FileNotFoundError: If the audio file does not exist.
    """
    import os
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    # Read file in executor to avoid blocking the event loop
    loop = asyncio.get_running_loop()

    def _read_file() -> bytes:
        with open(file_path, "rb") as f:
            return f.read()

    file_content = await loop.run_in_executor(None, _read_file)

    # Create a file-like object for the API
    from io import BytesIO
    audio_file = BytesIO(file_content)
    audio_file.name = os.path.basename(file_path)

    client = _get_client()
    transcript = await client.audio.transcriptions.create(
        model=settings.WHISPER_MODEL_NAME,
        file=audio_file
    )
    return transcript.text
