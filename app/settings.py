from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "pdf-extractor"
    MAX_FILE_MB: int = 20
    LOG_LEVEL: str = "info"
    CORS_ALLOW_ORIGINS: str = "*"  # comma-separated

    class Config:
        env_file = ".env"

settings = Settings()
