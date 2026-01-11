"""InvestmentStrategy model"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Numeric
from sqlalchemy.sql import func
from app.core.database import Base


class InvestmentStrategy(Base):
    """InvestmentStrategy model - 投資方針"""

    __tablename__ = "investment_strategies"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    name = Column(String(255), nullable=False, comment="方針名")
    style = Column(String(50), nullable=False, comment="投資スタイル")
    technical_indicators_priority = Column(
        JSON, nullable=True, comment="テクニカル指標の優先度設定"
    )
    fundamental_indicators_priority = Column(
        JSON, nullable=True, comment="ファンダメンタル指標の優先度設定"
    )
    risk_tolerance = Column(Integer, nullable=False, comment="リスク許容度（1-5）")
    investment_period = Column(String(20), nullable=False, comment="投資期間")
    target_yield = Column(Numeric(5, 2), nullable=True, comment="目標利回り（%）")
    stop_loss_line = Column(Numeric(5, 2), nullable=True, comment="損切ライン（%）")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="作成日時",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新日時",
    )

    def __repr__(self):
        return f"<InvestmentStrategy(id={self.id}, name={self.name}, style={self.style})>"
