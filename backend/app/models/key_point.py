"""KeyPoint model"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class KeyPoint(Base):
    """KeyPoint model - 見極めポイント"""

    __tablename__ = "key_points"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    evaluation_id = Column(
        Integer,
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False,
        comment="評価結果ID",
    )
    point_type = Column(String(20), nullable=False, comment="ポイントタイプ（buy/sell/caution）")
    description = Column(String(500), nullable=False, comment="説明")
    priority = Column(String(10), nullable=False, comment="優先度（high/medium/low）")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="作成日時",
    )

    def __repr__(self):
        return f"<KeyPoint(id={self.id}, type={self.point_type}, priority={self.priority})>"
