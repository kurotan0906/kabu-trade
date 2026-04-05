"""ChartAnalysis model"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class ChartAnalysis(Base):
    """ChartAnalysis model - チャート分析結果"""

    __tablename__ = "chart_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    symbol = Column(
        String(10),
        nullable=False,
        index=True,
        comment="銘柄コード（例: 7203）",
    )
    timeframe = Column(String(10), nullable=False, comment="時間足（例: 1D, 1W）")
    screenshot_path = Column(
        String(500), nullable=True, comment="スクリーンショットパス"
    )
    trend = Column(
        String(20), nullable=False, comment="トレンド（bullish/bearish/neutral）"
    )
    signals = Column(JSON, nullable=True, comment="シグナル詳細（JSON）")
    summary = Column(Text, nullable=False, comment="Claudeが生成したサマリー")
    recommendation = Column(
        String(10), nullable=False, comment="推奨（buy/sell/hold）"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="作成日時",
    )

    def __repr__(self):
        return (
            f"<ChartAnalysis(id={self.id}, symbol={self.symbol}, "
            f"timeframe={self.timeframe}, recommendation={self.recommendation})>"
        )
