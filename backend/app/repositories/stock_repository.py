"""Stock repository"""

from typing import List, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models.stock import Stock
from app.models.stock_price import StockPrice
from app.schemas.stock import StockInfo, StockPriceData


class StockRepository:
    """Stock repository - データアクセス層"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_code(self, code: str) -> Optional[Stock]:
        """
        銘柄コードで銘柄を検索
        
        Args:
            code: 銘柄コード
            
        Returns:
            Optional[Stock]: 銘柄情報（見つからない場合はNone）
        """
        result = await self.db.execute(select(Stock).where(Stock.code == code))
        return result.scalar_one_or_none()

    async def create_or_update(self, stock_info: StockInfo) -> Stock:
        """
        銘柄情報を作成または更新
        
        Args:
            stock_info: 銘柄情報
            
        Returns:
            Stock: 作成・更新された銘柄情報
        """
        stock = await self.find_by_code(stock_info.code)

        if stock:
            # 更新
            stock.name = stock_info.name
            stock.sector = stock_info.sector
            stock.market_cap = stock_info.market_cap
        else:
            # 作成
            stock = Stock(
                code=stock_info.code,
                name=stock_info.name,
                sector=stock_info.sector,
                market_cap=stock_info.market_cap,
            )
            self.db.add(stock)

        await self.db.commit()
        await self.db.refresh(stock)
        return stock

    async def save_prices(
        self, code: str, prices: List[StockPriceData]
    ) -> List[StockPrice]:
        """
        株価データを保存
        
        Args:
            code: 銘柄コード
            prices: 株価データのリスト
            
        Returns:
            List[StockPrice]: 保存された株価データ
        """
        saved_prices = []

        for price_data in prices:
            # 既存データを確認
            result = await self.db.execute(
                select(StockPrice).where(
                    and_(
                        StockPrice.stock_code == code,
                        StockPrice.date == price_data.date,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # 更新
                existing.open = price_data.open
                existing.high = price_data.high
                existing.low = price_data.low
                existing.close = price_data.close
                existing.volume = price_data.volume
                saved_prices.append(existing)
            else:
                # 作成
                new_price = StockPrice(
                    stock_code=code,
                    date=price_data.date,
                    open=price_data.open,
                    high=price_data.high,
                    low=price_data.low,
                    close=price_data.close,
                    volume=price_data.volume,
                )
                self.db.add(new_price)
                saved_prices.append(new_price)

        await self.db.commit()

        # リフレッシュ
        for price in saved_prices:
            await self.db.refresh(price)

        return saved_prices

    async def get_prices(
        self,
        code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[StockPrice]:
        """
        株価データを取得
        
        Args:
            code: 銘柄コード
            start_date: 開始日（オプション）
            end_date: 終了日（オプション）
            
        Returns:
            List[StockPrice]: 株価データのリスト
        """
        query = select(StockPrice).where(StockPrice.stock_code == code)

        if start_date:
            query = query.where(StockPrice.date >= start_date)
        if end_date:
            query = query.where(StockPrice.date <= end_date)

        query = query.order_by(StockPrice.date)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_latest_price(self, code: str) -> Optional[StockPrice]:
        """
        最新の株価データを取得
        
        Args:
            code: 銘柄コード
            
        Returns:
            Optional[StockPrice]: 最新の株価データ（見つからない場合はNone）
        """
        result = await self.db.execute(
            select(StockPrice)
            .where(StockPrice.stock_code == code)
            .order_by(StockPrice.date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
