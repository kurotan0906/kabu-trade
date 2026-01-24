from datetime import date

from app.services.api_selection_poc import PocErrorCategory, _classify_error
from app.core.exceptions import KabuStationAuthError, KabuStationRateLimitError
import httpx


def test_classify_auth_missing():
    cat, msg, hint = _classify_error(KabuStationAuthError())
    assert cat == PocErrorCategory.AUTH_MISSING
    assert hint is not None


def test_classify_rate_limit():
    cat, msg, hint = _classify_error(KabuStationRateLimitError())
    assert cat == PocErrorCategory.RATE_LIMIT


def test_classify_timeout():
    cat, msg, hint = _classify_error(httpx.TimeoutException("timeout"))
    assert cat == PocErrorCategory.TIMEOUT

