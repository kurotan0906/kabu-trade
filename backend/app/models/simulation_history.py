"""SimulationHistory model - 将来価値シミュレーション履歴"""

from sqlalchemy import Column, Integer, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class SimulationHistory(Base):
    __tablename__ = "simulation_histories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    input_json = Column(JSON, nullable=False, comment="リクエスト入力（pv/monthly/rate/years/goal）")
    result_json = Column(JSON, nullable=False, comment="計算結果（future_value/required_rate/timeseries）")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
