from app.config import settings


def test_openai_settings_exist():
    """Test that OpenAI and Whisper settings are added to config."""
    assert hasattr(settings, "OPENAI_API_KEY"), "OPENAI_API_KEY missing from settings"
    assert hasattr(settings, "OPENAI_MODEL_NAME"), "OPENAI_MODEL_NAME missing from settings"
    assert hasattr(settings, "WHISPER_MODEL_NAME"), "WHISPER_MODEL_NAME missing from settings"

    # Check default values
    assert settings.OPENAI_MODEL_NAME == "gpt-4o"
    assert settings.WHISPER_MODEL_NAME == "whisper-1"
