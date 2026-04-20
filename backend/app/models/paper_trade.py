"""PaperTrade models - 仮想売買の口座・保有・取引履歴"""

from sqlalchemy import Column, Integer, Float, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class PaperAccount(Base):
    """ペーパートレード仮想口座 (MVP では 1 行のみ)"""

    __tablename__ = "paper_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    initial_cash = Column(Float, nullable=False, comment="初期資金")
    cash_balance = Column(Float, nullable=False, comment="現在の仮想現金残高")
    started_at = Column(DateTime(timezone=True), nullable=False, comment="運用開始日")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PaperHolding(Base):
    """ペーパートレード保有銘柄"""

    __tablename__ = "paper_holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    name = Column(String(100), nullable=True)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("account_id", "symbol", name="uq_paper_holdings_account_symbol"),
    )


class PaperTrade(Base):
    """ペーパートレード取引履歴"""

    __tablename__ = "paper_trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    action = Column(String(4), nullable=False, comment="'buy' or 'sell'")
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    realized_pl = Column(Float, nullable=True, comment="sell のみ記録")
    executed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    note = Column(String(255), nullable=True)
    fee = Column(Float, nullable=True, comment="予約: MVP では常に NULL")
    dividend = Column(Float, nullable=True, comment="予約: MVP では常に NULL")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
