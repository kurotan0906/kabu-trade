"""tv_screener_client のユニットテスト（ネットワーク非依存部分）"""

import pytest

from app.external.tv_screener_client import _tv_to_symbol


@pytest.mark.parametrize(
    "ticker,expected",
    [
        ("TSE:7203", "7203.T"),
        ("TSE:6758", "6758.T"),
        ("TSE:285A", "285A.T"),
        ("NAG:1234", None),
        ("FSE:9999", None),
        ("SSE:5555", None),
        ("", None),
        ("7203", None),
        (":7203", None),
    ],
)
def test_tv_to_symbol(ticker, expected):
    assert _tv_to_symbol(ticker) == expected
