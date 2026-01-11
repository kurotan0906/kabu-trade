"""Application configuration"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "kabu-trade"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kabu_trade"
    REDIS_URL: str = "redis://localhost:6379/0"

    # kabuステーションAPI
    KABU_STATION_API_TOKEN: str = ""
    KABU_STATION_PASSWORD: str = ""
    KABU_STATION_API_URL: str = "https://localhost:18080/kabusapi"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
