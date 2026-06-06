from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Enterprise AI System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "enterprise_ai"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""

    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
