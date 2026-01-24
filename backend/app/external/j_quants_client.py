"""J-Quants API client (minimal, for PoC).

This client is intentionally minimal and focused on PoC connectivity checks.
It requires an ID token configured via environment variables and does not manage
refresh flows automatically.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.core.exceptions import ExternalAPIError


class JQuantsClient:
    def __init__(self):
        self.base_url = settings.JQUANTS_API_URL.rstrip("/")
        self.id_token = settings.JQUANTS_ID_TOKEN

    def _auth_headers(self) -> Dict[str, str]:
        if not self.id_token:
            raise ExternalAPIError("J-Quantsの認証トークンが未設定です（JQUANTS_ID_TOKEN）", error_code="JQUANTS_AUTH_ERROR")
        return {"Authorization": f"Bearer {self.id_token}"}

    async def get_listed_info(self) -> Dict[str, Any]:
        """Fetch listed issues info (used to validate JPX coverage).

        Note: Endpoint paths may evolve; callers should treat errors as evidence and record them.
        """
        url = f"{self.base_url}/listed/info"
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                r = await client.get(url, headers=self._auth_headers())
                r.raise_for_status()
                return r.json()
            except httpx.HTTPStatusError as e:
                raise ExternalAPIError(f"J-Quants API エラー: {e.response.status_code}", error_code="JQUANTS_API_ERROR")
            except httpx.RequestError as e:
                raise ExternalAPIError(f"J-Quants API 接続エラー: {str(e)}", error_code="JQUANTS_API_ERROR")

