"""kabuステーションAPI クライアント"""

import httpx
import ssl
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.exceptions import (
    KabuStationAPIError,
    KabuStationAuthError,
    KabuStationRateLimitError,
    MarketClosedError,
)


class KabuStationClient:
    """kabuステーションAPI クライアント"""

    def __init__(self):
        self.base_url = settings.KABU_STATION_API_URL
        self.api_token = settings.KABU_STATION_API_TOKEN
        self.password = settings.KABU_STATION_PASSWORD
        self._token: Optional[str] = None

        # SSL証明書の検証を無効化（ローカル環境用）
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def _get_token(self) -> str:
        """
        API Tokenを取得（認証）
        
        Returns:
            str: API Token
            
        Raises:
            KabuStationAuthError: 認証に失敗した場合
        """
        if self._token:
            return self._token

        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/token",
                    json={
                        "APIPassword": self.password,
                    },
                    headers={
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
                self._token = data.get("Token")
                if not self._token:
                    raise KabuStationAuthError("Token取得に失敗しました")
                return self._token
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise KabuStationAuthError("認証に失敗しました")
                error_text = e.response.text if hasattr(e.response, 'text') else str(e)
                raise KabuStationAPIError(f"Token取得エラー: {e.response.status_code} - {error_text}")
            except httpx.RequestError as e:
                raise KabuStationAPIError(f"API接続エラー: {str(e)}")
            except Exception as e:
                raise KabuStationAPIError(f"予期しないエラー: {str(e)}")

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        APIリクエストを実行
        
        Args:
            method: HTTPメソッド（GET, POST等）
            endpoint: APIエンドポイント
            params: クエリパラメータ
            json_data: リクエストボディ
            
        Returns:
            Dict[str, Any]: レスポンスデータ
            
        Raises:
            KabuStationAPIError: APIエラーの場合
            KabuStationRateLimitError: レート制限超過の場合
        """
        token = await self._get_token()

        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    params=params,
                    json=json_data,
                    headers={
                        "X-API-KEY": token,
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )

                # レート制限チェック
                if response.status_code == 429:
                    raise KabuStationRateLimitError()

                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    # Tokenが無効な場合、再取得を試みる
                    self._token = None
                    token = await self._get_token()
                    # 1回だけリトライ
                    response = await client.request(
                        method,
                        f"{self.base_url}{endpoint}",
                        params=params,
                        json=json_data,
                        headers={
                            "X-API-KEY": token,
                            "Content-Type": "application/json",
                        },
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    return response.json()
                elif e.response.status_code == 400:
                    error_data = e.response.json() if e.response.content else {}
                    error_message = error_data.get("Message", "APIリクエストエラー")
                    raise KabuStationAPIError(f"リクエストエラー: {error_message}")
                else:
                    raise KabuStationAPIError(
                        f"APIエラー: {e.response.status_code} - {e.response.text}"
                    )
            except httpx.RequestError as e:
                raise KabuStationAPIError(f"API接続エラー: {str(e)}")

    async def get_board(self, symbol: str, exchange: int = 1) -> Dict[str, Any]:
        """
        板情報を取得
        
        Args:
            symbol: 銘柄コード（例: "7203"）
            exchange: 市場コード（1: 東証, 3: 名証等）
            
        Returns:
            Dict[str, Any]: 板情報
        """
        return await self._request(
            "GET",
            "/board",
            params={"Symbol": symbol, "Exchange": exchange},
        )

    async def get_symbol_name(self, symbol: str, exchange: int = 1) -> Dict[str, Any]:
        """
        銘柄名を取得
        
        Args:
            symbol: 銘柄コード（例: "7203"）
            exchange: 市場コード（1: 東証, 3: 名証等）
            
        Returns:
            Dict[str, Any]: 銘柄名情報
        """
        return await self._request(
            "GET",
            "/symbolname",
            params={"Symbol": symbol, "Exchange": exchange},
        )

    async def get_daily_quotes(
        self,
        symbol: str,
        exchange: int = 1,
        period: int = 1,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        日足データを取得
        
        Args:
            symbol: 銘柄コード（例: "7203"）
            exchange: 市場コード（1: 東証, 3: 名証等）
            period: 期間（1: 日足, 2: 週足, 3: 月足）
            days: 取得日数
            
        Returns:
            Dict[str, Any]: 日足データ
        """
        return await self._request(
            "POST",
            "/dailyquotes",
            json_data={
                "Symbol": symbol,
                "Exchange": exchange,
                "Period": period,
                "Days": days,
            },
        )

    async def get_regulations(self, symbol: str, exchange: int = 1) -> Dict[str, Any]:
        """
        規制情報を取得
        
        Args:
            symbol: 銘柄コード（例: "7203"）
            exchange: 市場コード（1: 東証, 3: 名証等）
            
        Returns:
            Dict[str, Any]: 規制情報
        """
        return await self._request(
            "GET",
            "/regulations",
            params={"Symbol": symbol, "Exchange": exchange},
        )
