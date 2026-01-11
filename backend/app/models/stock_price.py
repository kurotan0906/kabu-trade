"""StockPrice model"""

from sqlalchemy import Column, Integer, String, Numeric, BigInteger, Date, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class StockPrice(Base):
    """StockPrice model - 株価データ"""

    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    stock_code = Column(
        String(10),
        ForeignKey("stocks.code", ondelete="CASCADE"),
        nullable=False,
        comment="銘柄コード",
    )
    date = Column(Date, nullable=False, comment="日付")
    open = Column(Numeric(10, 2), nullable=False, comment="始値")
    high = Column(Numeric(10, 2), nullable=False, comment="高値")
    low = Column(Numeric(10, 2), nullable=False, comment="安値")
    close = Column(Numeric(10, 2), nullable=False, comment="終値")
    volume = Column(BigInteger, nullable=False, comment="出来高")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="作成日時",
    )

    # 銘柄コードと日付の組み合わせでユニーク制約
    __table_args__ = (
        UniqueConstraint("stock_code", "date", name="uq_stock_price_code_date"),
    )

    def __repr__(self):
        return f"<StockPrice(stock_code={self.stock_code}, date={self.date}, close={self.close})>"
