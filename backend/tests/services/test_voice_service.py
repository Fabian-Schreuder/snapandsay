"""Tests for VoiceService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.voice_service import transcribe_audio


@pytest.mark.asyncio
async def test_transcribe_audio_success():
    """Test successful audio transcription."""
    mock_transcript = "A delicious apple"

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock()
    mock_client.audio.transcriptions.create.return_value.text = mock_transcript

    with (
        patch("os.path.exists", return_value=True),
        patch("app.services.voice_service._get_client", return_value=mock_client),
        patch("asyncio.get_running_loop") as mock_loop,
    ):
        # Mock the executor to run synchronously
        mock_loop.return_value.run_in_executor = AsyncMock(return_value=b"fake audio data")

        result = await transcribe_audio("test_audio.mp3", language="en")

        assert result == mock_transcript
        mock_client.audio.transcriptions.create.assert_called_once()


@pytest.mark.asyncio
async def test_transcribe_audio_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            await transcribe_audio("missing_audio.mp3", language="en")


@pytest.mark.asyncio
async def test_transcribe_audio_api_error():
    """Test that API errors are propagated."""
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(side_effect=Exception("API Error"))

    with (
        patch("os.path.exists", return_value=True),
        patch("app.services.voice_service._get_client", return_value=mock_client),
        patch("asyncio.get_running_loop") as mock_loop,
    ):
        mock_loop.return_value.run_in_executor = AsyncMock(return_value=b"fake audio data")

        with pytest.raises(Exception, match="API Error"):
            await transcribe_audio("test_audio.mp3", language="en")


@pytest.mark.asyncio
async def test_transcribe_audio_supabase_success():
    """Test successful transcription from Supabase storage."""
    mock_transcript = "Audio from Supabase"

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock()
    mock_client.audio.transcriptions.create.return_value.text = mock_transcript

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"fake audio content"

    mock_http_client = MagicMock()
    mock_http_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

    with (
        patch("os.path.exists", return_value=False),
        patch("app.services.voice_service._get_client", return_value=mock_client),
        patch("httpx.AsyncClient", return_value=mock_http_client),
        patch("app.config.settings.SUPABASE_URL", "https://supabase.co"),
    ):
        result = await transcribe_audio("remote/audio.wav", language="en", token="fake_token")  # noqa: S106

        assert result == mock_transcript
        mock_client.audio.transcriptions.create.assert_called_once()
        mock_http_client.__aenter__.return_value.get.assert_called_once()
