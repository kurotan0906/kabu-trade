"""StockScore model - バッチスコアリング結果"""

from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class StockScore(Base):
    """StockScore model - 全銘柄バッチスコアリング結果"""

    __tablename__ = "stock_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True, comment="銘柄コード（例: 7203.T）")
    name = Column(String(100), nullable=True, comment="銘柄名")
    sector = Column(String(100), nullable=True, comment="セクター")
    scored_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment="スコア算出日時")
    total_score = Column(Float, nullable=True, comment="総合スコア（0-100）")
    rating = Column(String(20), nullable=True, comment="レーティング（強い買い/買い/中立/売り/強い売り）")
    fundamental_score = Column(Float, nullable=True, comment="ファンダメンタルスコア（0-50）")
    technical_score = Column(Float, nullable=True, comment="テクニカルスコア（0-50）")
    kurotenko_score = Column(Float, nullable=True, comment="黒点子スコア（0-100）")
    kurotenko_criteria = Column(JSON, nullable=True, comment="黒点子条件合否")
    per = Column(Float, nullable=True)
    pbr = Column(Float, nullable=True)
    roe = Column(Float, nullable=True)
    dividend_yield = Column(Float, nullable=True)
    revenue_growth = Column(Float, nullable=True)
    ma_score = Column(Float, nullable=True)
    rsi_score = Column(Float, nullable=True)
    macd_score = Column(Float, nullable=True)
    close_price = Column(Float, nullable=True, comment="終値（バッチ取得時点）")
    data_quality = Column(String(20), nullable=False, default="ok", comment="ok/fetch_error/partial")

    def __repr__(self):
        return f"<StockScore(symbol={self.symbol}, total_score={self.total_score}, rating={self.rating})>"
