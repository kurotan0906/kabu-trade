"""Application configuration"""

from pydantic_settings import BaseSettings
from typing import List, Literal


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

    # Provider settings
    USE_MOCK_PROVIDER: bool = False  # モックプロバイダーを使用するか

    # Scoring data source
    # hybrid: yfinance の history + info を TradingView の指標で上書き（既定）
    # tv:     TradingView のみ（history が取れないため技術スコアは低下）
    # yfinance: yfinance のみ（従来動作）
    SCORING_DATA_SOURCE: Literal["hybrid", "tv", "yfinance"] = "hybrid"
    # yfinance は並列で叩くとレート制限で失敗しやすいため既定は 1（直列）
    SCORING_MAX_WORKERS: int = 1
    # バッチ時の yfinance 呼び出し間隔（秒）。>0 でスレッド間ロック付きスロットル（429 対策）
    SCORING_YFINANCE_MIN_INTERVAL_SEC: float = 0.0

    # J-Quants API (PoC)
    JQUANTS_API_URL: str = "https://api.jpx-jquants.com/v1"
    JQUANTS_ID_TOKEN: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        """CORS originsをリスト形式で取得"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
