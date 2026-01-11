"""Evaluation model"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Evaluation(Base):
    """Evaluation model - 評価結果"""

    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    stock_code = Column(
        String(10),
        ForeignKey("stocks.code", ondelete="CASCADE"),
        nullable=False,
        comment="銘柄コード",
    )
    strategy_id = Column(
        Integer,
        ForeignKey("investment_strategies.id", ondelete="SET NULL"),
        nullable=True,
        comment="投資方針ID（オプション）",
    )
    buy_score = Column(Integer, nullable=False, comment="買いスコア（0-100）")
    sell_score = Column(Integer, nullable=False, comment="売りスコア（0-100）")
    match_score = Column(Integer, nullable=True, comment="投資方針との適合度（0-100）")
    recommendation = Column(String(20), nullable=False, comment="推奨アクション")
    evaluation_date = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="評価日時",
    )
    details = Column(JSON, nullable=True, comment="評価詳細（JSON）")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="作成日時",
    )

    def __repr__(self):
        return f"<Evaluation(id={self.id}, stock_code={self.stock_code}, buy_score={self.buy_score}, sell_score={self.sell_score})>"
