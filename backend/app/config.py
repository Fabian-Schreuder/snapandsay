from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "SnapAndSay"

    # OpenAPI docs
    OPENAPI_URL: str = "/openapi.json"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    EXPIRE_ON_COMMIT: bool = False
    ECHO_SQL: bool = False

    # Auth
    SUPABASE_JWT_SECRET: str
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    SUPABASE_URL: str | None = None
    SUPABASE_AUTH_AUDIENCE: str = "authenticated"
    ADMIN_EMAILS: str = ""  # Comma separated emails

    # OpenAI
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL_NAME: str = "gpt-4o"
    WHISPER_MODEL_NAME: str = "whisper-1"

    # Email
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_FROM: str | None = None
    MAIL_SERVER: str | None = None
    MAIL_PORT: int | None = None
    MAIL_FROM_NAME: str = "FastAPI template"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = False
    VALIDATE_CERTS: bool = True
    TEMPLATE_DIR: str = "email_templates"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "https://snapandsay.vercel.app"]

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"), env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
