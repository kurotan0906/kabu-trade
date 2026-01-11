"""Stock schemas"""

from datetime import date as date_type, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class StockInfo(BaseModel):
    """銘柄情報スキーマ"""

    code: str = Field(..., description="銘柄コード", example="7203")
    name: str = Field(..., description="銘柄名", example="トヨタ自動車")
    sector: Optional[str] = Field(None, description="業種", example="自動車")
    market_cap: Optional[int] = Field(None, description="時価総額", example=35000000000000)
    current_price: Optional[Decimal] = Field(None, description="現在の株価", example=2500.0)
    per: Optional[Decimal] = Field(None, description="PER", example=12.5)
    pbr: Optional[Decimal] = Field(None, description="PBR", example=1.2)

    class Config:
        from_attributes = True


class StockPriceData(BaseModel):
    """株価データスキーマ"""

    date: date_type = Field(..., description="日付")
    open: Decimal = Field(..., description="始値")
    high: Decimal = Field(..., description="高値")
    low: Decimal = Field(..., description="安値")
    close: Decimal = Field(..., description="終値")
    volume: int = Field(..., description="出来高")

    class Config:
        from_attributes = True


class StockPriceResponse(BaseModel):
    """株価データレスポンススキーマ"""

    stock_code: str = Field(..., description="銘柄コード")
    stock_name: str = Field(..., description="銘柄名")
    period: str = Field(..., description="期間", example="1y")
    prices: List[StockPriceData] = Field(..., description="株価データリスト")

    class Config:
        from_attributes = True
