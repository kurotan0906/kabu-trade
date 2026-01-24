"""Repository layer.

Keep this package import-safe (avoid triggering DB initialization at import time).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["StockRepository"]

_LAZY: dict[str, tuple[str, str]] = {
    "StockRepository": ("app.repositories.stock_repository", "StockRepository"),
}


def __getattr__(name: str) -> Any:  # pragma: no cover
    if name in _LAZY:
        module_name, attr = _LAZY[name]
        return getattr(import_module(module_name), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
