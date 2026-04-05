"""ChartAnalysis schemas"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ChartAnalysisCreate(BaseModel):
    """チャート分析結果の作成リクエスト"""

    symbol: str = Field(..., description="銘柄コード（例: 7203）")
    timeframe: str = Field(..., description="時間足（例: 1D, 1W, 4H）")
    screenshot_path: Optional[str] = Field(None, description="スクリーンショットパス")
    trend: str = Field(..., description="トレンド（bullish/bearish/neutral）")
    signals: Optional[Dict[str, Any]] = Field(None, description="シグナル詳細")
    summary: str = Field(..., description="Claudeが生成したサマリー")
    recommendation: str = Field(..., description="推奨（buy/sell/hold）")


class ChartAnalysisResponse(BaseModel):
    """チャート分析結果のレスポンス"""

    id: int = Field(..., description="ID")
    symbol: str = Field(..., description="銘柄コード")
    timeframe: str = Field(..., description="時間足")
    screenshot_path: Optional[str] = Field(None, description="スクリーンショットパス")
    trend: str = Field(..., description="トレンド")
    signals: Optional[Dict[str, Any]] = Field(None, description="シグナル詳細")
    summary: str = Field(..., description="サマリー")
    recommendation: str = Field(..., description="推奨")
    created_at: datetime = Field(..., description="作成日時")

    class Config:
        from_attributes = True
