"""Portfolio models - 保有銘柄・設定・取引履歴"""

from sqlalchemy import Column, Integer, Float, String, DateTime, Date
from sqlalchemy.sql import func
from app.core.database import Base


class Holding(Base):
    """保有銘柄"""

    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True, comment="銘柄コード（例: 7203.T）")
    name = Column(String(100), nullable=True)
    quantity = Column(Integer, nullable=False, default=0, comment="保有株数")
    avg_price = Column(Float, nullable=False, default=0.0, comment="平均取得単価")
    purchase_date = Column(Date, nullable=True)
    # 'general' | 'nisa_growth' | 'nisa_tsumitate'
    account_type = Column(String(20), nullable=False, default="general")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PortfolioSetting(Base):
    """ポートフォリオ設定 (key-value)

    key 例:
      - target_amount        : 将来目標額 (float, yen)
      - target_deadline      : 目標達成希望日 (YYYY-MM-DD)
      - monthly_investment   : 毎月積立額 (float, yen)
      - nisa_used_current_year: 当年の NISA 成長枠使用額 (float, yen)
    """

    __tablename__ = "portfolio_settings"

    key = Column(String(50), primary_key=True)
    value = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TradeHistory(Base):
    """取引履歴"""

    __tablename__ = "trade_histories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    action = Column(String(10), nullable=False, comment="buy | sell")
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    account_type = Column(String(20), nullable=False, default="general")
    note = Column(String(255), nullable=True)
