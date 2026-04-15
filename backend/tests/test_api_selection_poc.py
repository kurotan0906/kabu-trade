from app.services.api_selection_poc import PocErrorCategory, _classify_error
import httpx


def test_classify_timeout():
    cat, msg, hint = _classify_error(httpx.TimeoutException("timeout"))
    assert cat == PocErrorCategory.TIMEOUT


def test_classify_network():
    cat, msg, hint = _classify_error(httpx.RequestError("network"))
    assert cat == PocErrorCategory.NETWORK
