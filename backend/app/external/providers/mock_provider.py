"""Mock stock data provider"""

from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
import random
from app.external.providers.base import StockDataProvider
from app.schemas.stock import StockInfo, StockPriceData
from app.core.exceptions import StockNotFoundError


class MockProvider(StockDataProvider):
    """Mock provider - モックデータプロバイダー（開発・テスト用）"""

    # サンプル銘柄データ
    MOCK_STOCKS = {
        "7203": {
            "name": "トヨタ自動車",
            "sector": "自動車",
            "market_cap": 35000000000000,
            "base_price": 2500.0,
        },
        "6758": {
            "name": "ソニーグループ",
            "sector": "エンターテインメント",
            "market_cap": 15000000000000,
            "base_price": 12000.0,
        },
        "9984": {
            "name": "ソフトバンクグループ",
            "sector": "通信",
            "market_cap": 8000000000000,
            "base_price": 6000.0,
        },
    }

    def __init__(self):
        pass

    async def get_stock_info(self, code: str) -> StockInfo:
        """
        銘柄情報を取得（モック）
        
        Args:
            code: 銘柄コード（例: "7203"）
            
        Returns:
            StockInfo: 銘柄情報
        """
        if code not in self.MOCK_STOCKS:
            raise StockNotFoundError(code)

        stock_data = self.MOCK_STOCKS[code]
        # 現在価格はベース価格にランダムな変動を加える
        current_price = Decimal(
            str(stock_data["base_price"] * (1 + random.uniform(-0.05, 0.05)))
        )

        return StockInfo(
            code=code,
            name=stock_data["name"],
            sector=stock_data["sector"],
            market_cap=stock_data["market_cap"],
            current_price=current_price,
            per=Decimal("12.5") if code == "7203" else Decimal("15.0"),
            pbr=Decimal("1.2") if code == "7203" else Decimal("1.5"),
        )

    async def get_stock_prices(
        self,
        code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: Optional[str] = None,
    ) -> List[StockPriceData]:
        """
        株価データを取得（モック）
        
        Args:
            code: 銘柄コード（例: "7203"）
            start_date: 開始日（オプション）
            end_date: 終了日（オプション）
            period: 期間（"1d", "1w", "1m", "3m", "6m", "1y"）（オプション）
            
        Returns:
            List[StockPriceData]: 株価データのリスト
        """
        if code not in self.MOCK_STOCKS:
            raise StockNotFoundError(code)

        stock_data = self.MOCK_STOCKS[code]
        base_price = stock_data["base_price"]

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

        # モックデータを生成（過去から現在まで）
        prices = []
        current_date = start
        current_price = base_price * (1 + random.uniform(-0.2, 0.2))

        while current_date <= end:
            # 週末をスキップ（簡易実装）
            if current_date.weekday() < 5:  # 月曜日=0, 金曜日=4
                # 前日の価格をベースに変動
                change_rate = random.uniform(-0.03, 0.03)
                current_price = current_price * (1 + change_rate)

                # OHLCデータを生成
                daily_volatility = random.uniform(0.01, 0.02)
                open_price = current_price * (1 + random.uniform(-daily_volatility, daily_volatility))
                high_price = max(open_price, current_price) * (1 + random.uniform(0, daily_volatility))
                low_price = min(open_price, current_price) * (1 - random.uniform(0, daily_volatility))
                close_price = current_price

                # 出来高を生成
                volume = random.randint(1000000, 10000000)

                prices.append(
                    StockPriceData(
                        date=current_date,
                        open=Decimal(str(round(open_price, 2))),
                        high=Decimal(str(round(high_price, 2))),
                        low=Decimal(str(round(low_price, 2))),
                        close=Decimal(str(round(close_price, 2))),
                        volume=volume,
                    )
                )

                current_price = close_price

            current_date += timedelta(days=1)

        return prices

    async def get_realtime_price(self, code: str) -> Decimal:
        """
        リアルタイム株価を取得（モック）
        
        Args:
            code: 銘柄コード（例: "7203"）
            
        Returns:
            Decimal: 現在の株価
        """
        stock_info = await self.get_stock_info(code)
        return stock_info.current_price or Decimal("0")

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
