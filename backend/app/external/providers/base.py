"""Base provider for stock data"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from app.schemas.stock import StockInfo, StockPriceData


class StockDataProvider(ABC):
    """抽象クラス: 株価データプロバイダー"""

    @abstractmethod
    async def get_stock_info(self, code: str) -> StockInfo:
        """
        銘柄情報を取得
        
        Args:
            code: 銘柄コード（例: "7203"）
            
        Returns:
            StockInfo: 銘柄情報
            
        Raises:
            StockNotFoundError: 銘柄が見つからない場合
            ExternalAPIError: 外部APIエラーの場合
        """
        pass

    @abstractmethod
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
            
        Raises:
            StockNotFoundError: 銘柄が見つからない場合
            ExternalAPIError: 外部APIエラーの場合
        """
        pass

    @abstractmethod
    async def get_realtime_price(self, code: str) -> Decimal:
        """
        リアルタイム株価を取得
        
        Args:
            code: 銘柄コード（例: "7203"）
            
        Returns:
            Decimal: 現在の株価
            
        Raises:
            StockNotFoundError: 銘柄が見つからない場合
            ExternalAPIError: 外部APIエラーの場合
            MarketClosedError: 市場が休場中の場合
        """
        pass
