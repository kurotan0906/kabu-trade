"""Evaluation schemas"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TechnicalIndicatorsResponse(BaseModel):
    """テクニカル指標レスポンススキーマ"""

    moving_averages: Dict[str, float] = Field(..., description="移動平均線")
    rsi: float = Field(..., description="RSI")
    macd: Dict[str, float] = Field(..., description="MACD")
    bollinger_bands: Dict[str, float] = Field(..., description="ボリンジャーバンド")
    support_resistance: Dict[str, float] = Field(..., description="サポート・レジスタンス")


class FundamentalMetricsResponse(BaseModel):
    """ファンダメンタル指標レスポンススキーマ"""

    score: int = Field(..., description="スコア（0-100）")
    evaluation: str = Field(..., description="評価")
    per_evaluation: Dict[str, Any] = Field(..., description="PER評価")
    pbr_evaluation: Dict[str, Any] = Field(..., description="PBR評価")
    descriptions: List[str] = Field(..., description="説明リスト")


class BuySignalResponse(BaseModel):
    """買いシグナルレスポンススキーマ"""

    score: int = Field(..., description="買いスコア（0-100）")
    recommendation: str = Field(..., description="推奨度（強力/推奨/注意/非推奨）")
    reasons: List[str] = Field(..., description="理由リスト")


class SellSignalResponse(BaseModel):
    """売りシグナルレスポンススキーマ"""

    score: int = Field(..., description="売りスコア（0-100）")
    recommendation: str = Field(..., description="推奨度（強力/推奨/注意/様子見）")
    reasons: List[str] = Field(..., description="理由リスト")


class EvaluationResult(BaseModel):
    """評価結果スキーマ"""

    id: Optional[int] = Field(None, description="評価ID")
    stock_code: str = Field(..., description="銘柄コード")
    stock_name: str = Field(..., description="銘柄名")
    buy_score: int = Field(..., description="買いスコア（0-100）")
    sell_score: int = Field(..., description="売りスコア（0-100）")
    buy_recommendation: str = Field(..., description="買い推奨度")
    sell_recommendation: str = Field(..., description="売り推奨度")
    technical_indicators: TechnicalIndicatorsResponse = Field(..., description="テクニカル指標")
    fundamental_metrics: FundamentalMetricsResponse = Field(..., description="ファンダメンタル指標")
    buy_signal: BuySignalResponse = Field(..., description="買いシグナル")
    sell_signal: SellSignalResponse = Field(..., description="売りシグナル")
    evaluation_date: datetime = Field(..., description="評価日時")

    class Config:
        from_attributes = True
