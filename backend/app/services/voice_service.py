"""Voice transcription service using OpenAI Whisper."""
import asyncio
from functools import lru_cache
from openai import AsyncOpenAI
from app.config import settings


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    """Lazily instantiate and cache the OpenAI client."""
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def transcribe_audio(file_path: str, token: str | None = None) -> str:
    """
    Transcribe an audio file using OpenAI Whisper.

    Args:
        file_path: Path to the audio file (local path or Supabase storage path).
        token: Optional user JWT for accessing restricted Supabase storage.

    Returns:
        The transcribed text.

    Raises:
        FileNotFoundError: If the audio file does not exist.
    """
    import os
    from io import BytesIO
    import httpx

    audio_file = None

    # 1. Try local file first
    if os.path.exists(file_path):
        # Read file in executor to avoid blocking
        loop = asyncio.get_running_loop()
        def _read_file() -> bytes:
            with open(file_path, "rb") as f:
                return f.read()
        
        file_content = await loop.run_in_executor(None, _read_file)
        audio_file = BytesIO(file_content)
        audio_file.name = os.path.basename(file_path)

    # 2. Try Supabase Storage if token provided
    elif token and settings.SUPABASE_URL:
        # Construct authenticated storage URL
        # Assumption: file_path is relative to the bucket (e.g. "user_id/filename.webm")
        url = f"{settings.SUPABASE_URL}/storage/v1/object/authenticated/raw_uploads/{file_path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, 
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise FileNotFoundError(
                    f"Audio file not found in storage: {file_path} "
                    f"(Status: {response.status_code})"
                )
            
            audio_file = BytesIO(response.content)
            audio_file.name = os.path.basename(file_path)

    if not audio_file:
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    client = _get_client()
    transcript = await client.audio.transcriptions.create(
        model=settings.WHISPER_MODEL_NAME,
        file=audio_file
    )
    return transcript.text
