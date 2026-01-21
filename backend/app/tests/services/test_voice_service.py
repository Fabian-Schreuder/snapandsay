import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from app.config import settings
from app.services.voice_service import transcribe_audio


@pytest.mark.asyncio
async def test_transcribe_audio_uses_language_param():
    # Create a dummy file
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(b"dummy audio data")
        temp_path = f.name

    try:
        mock_client = AsyncMock()
        # Mock the create method
        mock_create = AsyncMock()
        mock_create.return_value.text = "Gezellig"

        # Setup the chain: client.audio.transcriptions.create
        mock_client.audio.transcriptions.create = mock_create

        with patch("app.services.voice_service._get_client", return_value=mock_client):
            # Act
            transcript = await transcribe_audio(temp_path, language="nl")

            # Assert
            assert transcript == "Gezellig"

            # Verify call args
            call_args = mock_create.call_args
            assert call_args is not None
            _, kwargs = call_args
            assert kwargs["language"] == "nl"
            assert kwargs["model"] == settings.WHISPER_MODEL_NAME

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@pytest.mark.asyncio
async def test_transcribe_audio_uses_english_param():
    # Create a dummy file
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(b"dummy audio data")
        temp_path = f.name

    try:
        mock_client = AsyncMock()
        mock_create = AsyncMock()
        mock_create.return_value.text = "Hello"
        mock_client.audio.transcriptions.create = mock_create

        with patch("app.services.voice_service._get_client", return_value=mock_client):
            # Act
            transcript = await transcribe_audio(temp_path, language="en")

            # Assert
            assert transcript == "Hello"

            # Verify call args
            _, kwargs = mock_create.call_args
            assert kwargs["language"] == "en"

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
