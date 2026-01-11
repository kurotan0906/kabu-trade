"""Stock service - ビジネスロジック層"""

from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.stock_repository import StockRepository
from app.external.providers.kabu_station import KabuStationProvider
from app.core.redis_client import get_redis
from app.schemas.stock import StockInfo, StockPriceData
from app.core.exceptions import StockNotFoundError
import json


class StockService:
    """Stock service - 株情報サービス"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = StockRepository(db)
        self.provider = KabuStationProvider()

    async def _get_cache(self, key: str) -> Optional[dict]:
        """キャッシュからデータを取得"""
        redis = await get_redis()
        cached = await redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def _set_cache(self, key: str, value: dict, ttl: int = 300):
        """キャッシュにデータを保存"""
        redis = await get_redis()
        await redis.setex(key, ttl, json.dumps(value, default=str))

    async def get_stock_info(self, code: str, use_cache: bool = True) -> StockInfo:
        """
        銘柄情報を取得
        
        Args:
            code: 銘柄コード
            use_cache: キャッシュを使用するか
            
        Returns:
            StockInfo: 銘柄情報
        """
        cache_key = f"stock:{code}:info"

        # キャッシュ確認
        if use_cache:
            cached = await self._get_cache(cache_key)
            if cached:
                return StockInfo(**cached)

        # DB確認
        stock = await self.repository.find_by_code(code)
        if stock:
            # DBからStockInfoを構築
            stock_info = StockInfo(
                code=stock.code,
                name=stock.name,
                sector=stock.sector,
                market_cap=stock.market_cap,
                current_price=None,  # リアルタイム価格は別途取得
                per=None,
                pbr=None,
            )

            # リアルタイム価格を取得
            try:
                current_price = await self.provider.get_realtime_price(code)
                stock_info.current_price = current_price
            except Exception:
                # リアルタイム価格取得失敗時は最新のDB価格を使用
                latest_price = await self.repository.get_latest_price(code)
                if latest_price:
                    stock_info.current_price = latest_price.close

            # キャッシュに保存（1時間）
            await self._set_cache(cache_key, stock_info.dict(), ttl=3600)

            return stock_info

        # 外部APIから取得
        stock_info = await self.provider.get_stock_info(code)

        # DBに保存
        await self.repository.create_or_update(stock_info)

        # キャッシュに保存（1時間）
        await self._set_cache(cache_key, stock_info.dict(), ttl=3600)

        return stock_info

    async def get_stock_prices(
        self,
        code: str,
        period: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True,
    ) -> List[StockPriceData]:
        """
        株価データを取得
        
        Args:
            code: 銘柄コード
            period: 期間（"1d", "1w", "1m", "3m", "6m", "1y"）
            start_date: 開始日
            end_date: 終了日
            use_cache: キャッシュを使用するか
            
        Returns:
            List[StockPriceData]: 株価データのリスト
        """
        # キャッシュキーを生成
        cache_key = f"stock:{code}:prices:{period or f'{start_date}_{end_date}'}"

        # キャッシュ確認
        if use_cache:
            cached = await self._get_cache(cache_key)
            if cached:
                return [StockPriceData(**p) for p in cached]

        # 期間を計算
        if period:
            end = date.today()
            days = self._parse_period_to_days(period)
            start = end - timedelta(days=days)
        elif start_date and end_date:
            start = start_date
            end = end_date
        else:
            # デフォルト: 1年
            end = date.today()
            start = end - timedelta(days=365)

        # DBから取得を試みる
        db_prices = await self.repository.get_prices(code, start, end)

        # データが十分にある場合はDBから返す
        if len(db_prices) > 0:
            # 最新データが1日以内ならDBから返す
            latest_date = max(p.date for p in db_prices)
            if (date.today() - latest_date).days <= 1:
                prices = [
                    StockPriceData(
                        date=p.date,
                        open=p.open,
                        high=p.high,
                        low=p.low,
                        close=p.close,
                        volume=p.volume,
                    )
                    for p in db_prices
                ]

                # キャッシュに保存（1時間）
                await self._set_cache(
                    cache_key, [p.dict() for p in prices], ttl=3600
                )

                return prices

        # 外部APIから取得
        prices = await self.provider.get_stock_prices(
            code, start_date=start, end_date=end, period=period
        )

        # DBに保存
        if prices:
            await self.repository.save_prices(code, prices)

        # キャッシュに保存（1時間）
        if prices:
            await self._set_cache(
                cache_key, [p.dict() for p in prices], ttl=3600
            )

        return prices

    def _parse_period_to_days(self, period: str) -> int:
        """期間文字列を日数に変換"""
        period_map = {
            "1d": 1,
            "1w": 7,
            "1m": 30,
            "3m": 90,
            "6m": 180,
            "1y": 365,
        }
        return period_map.get(period, 365)
