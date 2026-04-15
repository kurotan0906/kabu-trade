"""Custom exceptions"""

from fastapi import HTTPException, status


class KabuTradeException(HTTPException):
    """Base exception for Kabu Trade application"""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An error occurred",
        error_code: str = None,
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


class StockNotFoundError(KabuTradeException):
    """Stock not found exception"""

    def __init__(self, stock_code: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"銘柄コード {stock_code} が見つかりません",
            error_code="STOCK_NOT_FOUND",
        )


class ExternalAPIError(KabuTradeException):
    """External API error exception"""

    def __init__(self, message: str, error_code: str = "EXTERNAL_API_ERROR"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=message,
            error_code=error_code,
        )


class MarketClosedError(KabuTradeException):
    """Market closed exception"""

    def __init__(self, message: str = "市場は休場中です"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            error_code="MARKET_CLOSED",
        )
