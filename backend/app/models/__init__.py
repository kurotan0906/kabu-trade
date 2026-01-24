"""Database models.

Keep this package import-safe (avoid importing DB engine/mappings at import time).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["Stock", "StockPrice", "Evaluation", "InvestmentStrategy", "KeyPoint"]

_LAZY: dict[str, tuple[str, str]] = {
    "Stock": ("app.models.stock", "Stock"),
    "StockPrice": ("app.models.stock_price", "StockPrice"),
    "Evaluation": ("app.models.evaluation", "Evaluation"),
    "InvestmentStrategy": ("app.models.investment_strategy", "InvestmentStrategy"),
    "KeyPoint": ("app.models.key_point", "KeyPoint"),
}


def __getattr__(name: str) -> Any:  # pragma: no cover
    if name in _LAZY:
        module_name, attr = _LAZY[name]
        return getattr(import_module(module_name), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
