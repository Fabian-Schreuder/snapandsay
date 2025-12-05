from pathlib import Path

import pytest
from fastapi_mail import ConnectionConfig

from app.email import get_email_config


@pytest.fixture
def mock_settings(mocker):
    mock = mocker.patch("app.email.settings")
    # Set up mock settings with test values
    mock.MAIL_USERNAME = "test_user"
    mock.MAIL_PASSWORD = "test_pass"
    mock.MAIL_FROM = "test@example.com"
    mock.MAIL_PORT = 587
    mock.MAIL_SERVER = "smtp.test.com"
    mock.MAIL_FROM_NAME = "Test Sender"
    mock.MAIL_STARTTLS = True
    mock.MAIL_SSL_TLS = False
    mock.USE_CREDENTIALS = True
    mock.VALIDATE_CERTS = True
    mock.TEMPLATE_DIR = "email_templates"
    mock.FRONTEND_URL = "http://test-frontend.com"
    return mock


def test_get_email_config(mock_settings):
    config = get_email_config()

    assert isinstance(config, ConnectionConfig)
    assert config.MAIL_USERNAME == "test_user"
    assert config.MAIL_PASSWORD == "test_pass"
    assert config.MAIL_FROM == "test@example.com"
    assert config.MAIL_PORT == 587
    assert config.MAIL_SERVER == "smtp.test.com"
    assert config.MAIL_FROM_NAME == "Test Sender"
    assert config.MAIL_STARTTLS
    assert not config.MAIL_SSL_TLS
    assert config.USE_CREDENTIALS
    assert config.VALIDATE_CERTS
    assert isinstance(config.TEMPLATE_FOLDER, Path)
