"""Stock model"""

from sqlalchemy import Column, String, BigInteger, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Stock(Base):
    """Stock model - 銘柄情報"""

    __tablename__ = "stocks"

    code = Column(String(10), primary_key=True, comment="銘柄コード")
    name = Column(String(255), nullable=False, comment="銘柄名")
    sector = Column(String(100), nullable=True, comment="業種")
    market_cap = Column(BigInteger, nullable=True, comment="時価総額")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="作成日時",
    )

    def __repr__(self):
        return f"<Stock(code={self.code}, name={self.name})>"
