"""Business logic services.

Keep this package import-safe:
- Avoid importing DB/engine initialization on import.
- Provide lazy exports for convenience.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "StockService",
    "build_candidate_evaluation",
    "PocRunResult",
    "PocErrorCategory",
    "run_kabu_station_poc",
    "run_jquants_poc",
]

_LAZY: dict[str, tuple[str, str]] = {
    "StockService": ("app.services.stock_service", "StockService"),
    "build_candidate_evaluation": ("app.services.api_selection_service", "build_candidate_evaluation"),
    "PocRunResult": ("app.services.api_selection_poc", "PocRunResult"),
    "PocErrorCategory": ("app.services.api_selection_poc", "PocErrorCategory"),
    "run_kabu_station_poc": ("app.services.api_selection_poc", "run_kabu_station_poc"),
    "run_jquants_poc": ("app.services.api_selection_poc", "run_jquants_poc"),
}


def __getattr__(name: str) -> Any:  # pragma: no cover
    if name in _LAZY:
        module_name, attr = _LAZY[name]
        return getattr(import_module(module_name), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
