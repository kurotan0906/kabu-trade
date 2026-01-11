"""kabuステーションAPI プロバイダー"""

from typing import List, Optional, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal
from app.external.providers.base import StockDataProvider
from app.external.kabu_station_client import KabuStationClient
from app.schemas.stock import StockInfo, StockPriceData
from app.core.exceptions import StockNotFoundError, MarketClosedError


class KabuStationProvider(StockDataProvider):
    """kabuステーションAPIを使用した株価データプロバイダー"""

    def __init__(self):
        self.client = KabuStationClient()

    def _parse_exchange(self, code: str) -> Tuple[str, int]:
        """
        銘柄コードから市場コードを判定
        
        Args:
            code: 銘柄コード
            
        Returns:
            Tuple[str, int]: (銘柄コード, 市場コード)
        """
        # 名証の銘柄コードは通常4桁で、特定の範囲に含まれる
        # 簡易的な判定（実際の実装ではより詳細な判定が必要）
        # 東証: 1, 名証: 3
        # デフォルトは東証とする
        return code, 1

    def _parse_period_to_days(self, period: str) -> int:
        """
        期間文字列を日数に変換
        
        Args:
            period: 期間（"1d", "1w", "1m", "3m", "6m", "1y"）
            
        Returns:
            int: 日数
        """
        period_map = {
            "1d": 1,
            "1w": 7,
            "1m": 30,
            "3m": 90,
            "6m": 180,
            "1y": 365,
        }
        return period_map.get(period, 365)

    async def get_stock_info(self, code: str) -> StockInfo:
        """
        銘柄情報を取得
        
        Args:
            code: 銘柄コード（例: "7203"）
            
        Returns:
            StockInfo: 銘柄情報
        """
        try:
            symbol, exchange = self._parse_exchange(code)

            # 銘柄名を取得
            name_data = await self.client.get_symbol_name(symbol, exchange)
            name = name_data.get("SymbolName", "")

            # 板情報を取得（現在の株価を含む）
            board_data = await self.client.get_board(symbol, exchange)
            current_price = Decimal(str(board_data.get("CurrentPrice", 0)))

            # 基本情報を構築
            # 注: kabuステーションAPIではPER、PBR等は別エンドポイントで取得が必要
            return StockInfo(
                code=code,
                name=name,
                sector=None,  # TODO: 別エンドポイントで取得
                market_cap=None,  # TODO: 別エンドポイントで取得
                current_price=current_price,
                per=None,  # TODO: 別エンドポイントで取得
                pbr=None,  # TODO: 別エンドポイントで取得
            )
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                raise StockNotFoundError(code)
            raise

    async def get_stock_prices(
        self,
        code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: Optional[str] = None,
    ) -> List[StockPriceData]:
        """
        株価データを取得
        
        Args:
            code: 銘柄コード（例: "7203"）
            start_date: 開始日（オプション）
            end_date: 終了日（オプション）
            period: 期間（"1d", "1w", "1m", "3m", "6m", "1y"）（オプション）
            
        Returns:
            List[StockPriceData]: 株価データのリスト
        """
        try:
            symbol, exchange = self._parse_exchange(code)

            # 期間から日数を計算
            if period:
                days = self._parse_period_to_days(period)
            elif start_date and end_date:
                days = (end_date - start_date).days
            else:
                days = 365  # デフォルト1年

            # 日足データを取得
            data = await self.client.get_daily_quotes(
                symbol=symbol,
                exchange=exchange,
                period=1,  # 日足
                days=days,
            )

            # データを変換
            prices = []
            daily_quotes = data.get("DailyQuotes", [])

            for quote in daily_quotes:
                prices.append(
                    StockPriceData(
                        date=datetime.strptime(quote["Date"], "%Y-%m-%d").date(),
                        open=Decimal(str(quote.get("Open", 0))),
                        high=Decimal(str(quote.get("High", 0))),
                        low=Decimal(str(quote.get("Low", 0))),
                        close=Decimal(str(quote.get("Close", 0))),
                        volume=int(quote.get("Volume", 0)),
                    )
                )

            # 日付順にソート
            prices.sort(key=lambda x: x.date)

            return prices
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                raise StockNotFoundError(code)
            raise

    async def get_realtime_price(self, code: str) -> Decimal:
        """
        リアルタイム株価を取得
        
        Args:
            code: 銘柄コード（例: "7203"）
            
        Returns:
            Decimal: 現在の株価
        """
        try:
            symbol, exchange = self._parse_exchange(code)

            # 板情報を取得
            board_data = await self.client.get_board(symbol, exchange)

            # 規制情報を確認（市場休場チェック）
            regulations = await self.client.get_regulations(symbol, exchange)
            if regulations.get("Regulations"):
                raise MarketClosedError("市場は休場中です")

            current_price = Decimal(str(board_data.get("CurrentPrice", 0)))
            if current_price == 0:
                raise StockNotFoundError(code)

            return current_price
        except MarketClosedError:
            raise
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                raise StockNotFoundError(code)
            raise
