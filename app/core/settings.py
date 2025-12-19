from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_PORT: str = "8080"

    # OpenAI / OpenRouter
    OPENAI_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None
    LLM_MODEL: str = "openai/gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 256

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore any other env vars not declared above
    )


settings = Settings()
