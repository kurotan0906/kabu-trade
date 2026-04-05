"""TradingViewSignal model - TradingView MCP テクニカル分析結果"""

from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class TradingViewSignal(Base):
    """TradingView MCP で取得したテクニカル分析結果"""

    __tablename__ = "tradingview_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True, comment="銘柄コード（例: 7203、.T なし）")
    recommendation = Column(String(20), nullable=True, comment="STRONG_BUY/BUY/NEUTRAL/SELL/STRONG_SELL")
    score = Column(Float, nullable=True, comment="0-100 変換スコア")
    buy_count = Column(Integer, nullable=True, comment="買いシグナル数")
    sell_count = Column(Integer, nullable=True, comment="売りシグナル数")
    neutral_count = Column(Integer, nullable=True, comment="中立シグナル数")
    ma_recommendation = Column(String(20), nullable=True, comment="移動平均サマリー")
    osc_recommendation = Column(String(20), nullable=True, comment="オシレーターサマリー")
    details = Column(JSON, nullable=True, comment="全指標の生データ")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<TradingViewSignal(symbol={self.symbol}, recommendation={self.recommendation})>"
