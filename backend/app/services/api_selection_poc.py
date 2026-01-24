"""PoC runner for API selection.

Runs lightweight connectivity checks against candidate APIs and records classified outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

import httpx

from app.core.exceptions import (
    ExternalAPIError,
    KabuStationAuthError,
    KabuStationRateLimitError,
)
from app.external.j_quants_client import JQuantsClient
from app.external.providers.kabu_station import KabuStationProvider
from app.external.providers.base import StockDataProvider


class PocErrorCategory(str, Enum):
    AUTH_MISSING = "auth_missing"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    NETWORK = "network"
    OTHER = "other"


@dataclass(frozen=True)
class PocRunResult:
    provider_name: str
    ok: bool
    checked_at: date
    error_category: Optional[PocErrorCategory] = None
    message: Optional[str] = None
    required_auth_hint: Optional[str] = None


def _classify_error(e: Exception) -> tuple[PocErrorCategory, str, Optional[str]]:
    if isinstance(e, (KabuStationAuthError,)):
        return PocErrorCategory.AUTH_MISSING, str(e.detail), "KABU_STATION_PASSWORD"
    if isinstance(e, (KabuStationRateLimitError,)):
        return PocErrorCategory.RATE_LIMIT, str(e.detail), None
    if isinstance(e, ExternalAPIError):
        # Use error_code heuristics when available
        if getattr(e, "error_code", "") in ("JQUANTS_AUTH_ERROR",):
            return PocErrorCategory.AUTH_MISSING, str(e.detail), "JQUANTS_ID_TOKEN"
        return PocErrorCategory.OTHER, str(e.detail), None
    if isinstance(e, httpx.TimeoutException):
        return PocErrorCategory.TIMEOUT, str(e), None
    if isinstance(e, httpx.RequestError):
        return PocErrorCategory.NETWORK, str(e), None
    return PocErrorCategory.OTHER, str(e), None


async def run_provider_poc(provider: StockDataProvider, *, stock_code: str, checked_at: date) -> PocRunResult:
    """Generic PoC runner for StockDataProvider implementations."""
    try:
        _ = await provider.get_stock_info(stock_code)
        _ = await provider.get_stock_prices(stock_code, period="1m")
        _ = await provider.get_realtime_price(stock_code)
        return PocRunResult(provider_name=provider.__class__.__name__, ok=True, checked_at=checked_at)
    except Exception as e:
        cat, msg, hint = _classify_error(e)
        return PocRunResult(
            provider_name=provider.__class__.__name__,
            ok=False,
            checked_at=checked_at,
            error_category=cat,
            message=msg,
            required_auth_hint=hint,
        )


async def run_kabu_station_poc(*, stock_code: str, checked_at: date) -> PocRunResult:
    """PoC for existing kabuステーション candidate."""
    provider = KabuStationProvider()
    return await run_provider_poc(provider, stock_code=stock_code, checked_at=checked_at)


async def run_jquants_poc(*, checked_at: date) -> PocRunResult:
    """PoC for a JPX-family free-start candidate (J-Quants).

    This is a minimal reachability check (listed info endpoint) and will fail safely
    when auth is not configured.
    """
    client = JQuantsClient()
    try:
        _ = await client.get_listed_info()
        return PocRunResult(provider_name="JQuantsClient", ok=True, checked_at=checked_at)
    except Exception as e:
        cat, msg, hint = _classify_error(e)
        return PocRunResult(
            provider_name="JQuantsClient",
            ok=False,
            checked_at=checked_at,
            error_category=cat,
            message=msg,
            required_auth_hint=hint,
        )

