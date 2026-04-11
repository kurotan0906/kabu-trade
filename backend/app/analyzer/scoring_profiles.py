"""スコアリングプロファイル - stock-advisor/analyzer/scoring_profiles.py から移植

3 種類の投資プロファイルで指標の重みとしきい値を切替える。
compute_phase_score() は StockScore ORM または互換 dataclass を受け取り、
0〜100 の phase_score を返す（DB 書き込みなし）。
"""

from dataclasses import dataclass
from typing import Any


PBR_THRESHOLDS = [(0.8, 1.0), (1.0, 0.7), (1.5, 0.4)]


def _normalize_max(value, thresholds: list) -> float:
    if value is None:
        return 0.5
    for max_val, score in sorted(thresholds, key=lambda x: x[0]):
        if value <= max_val:
            return score
    return 0.0


def _normalize_min(value, thresholds: list) -> float:
    if value is None:
        return 0.5
    for min_val, score in sorted(thresholds, key=lambda x: x[0], reverse=True):
        if value >= min_val:
            return score
    return 0.0


def _normalize_pbr(value) -> float:
    if value is None or value <= 0:
        return 0.5
    return _normalize_max(value, PBR_THRESHOLDS)


@dataclass
class ScoringProfile:
    name: str
    fundamental_split: float
    per_weight: float
    pbr_weight: float
    roe_weight: float
    dividend_weight: float
    growth_weight: float
    per_thresholds: list
    roe_thresholds: list
    dividend_thresholds: list
    growth_thresholds: list


_ROE_THRESHOLDS = [(0.20, 1.0), (0.15, 0.7), (0.10, 0.4)]


GROWTH_PROFILE = ScoringProfile(
    name="成長型",
    fundamental_split=0.40,
    per_weight=0.20, pbr_weight=0.10, roe_weight=0.30,
    dividend_weight=0.10, growth_weight=0.30,
    per_thresholds=[(15, 1.0), (25, 0.7), (40, 0.4)],
    roe_thresholds=_ROE_THRESHOLDS,
    dividend_thresholds=[(0.03, 1.0), (0.02, 0.7), (0.01, 0.4)],
    growth_thresholds=[(0.30, 1.0), (0.15, 0.7), (0.00, 0.4)],
)

BALANCED_PROFILE = ScoringProfile(
    name="バランス型",
    fundamental_split=0.50,
    per_weight=0.20, pbr_weight=0.20, roe_weight=0.20,
    dividend_weight=0.20, growth_weight=0.20,
    per_thresholds=[(10, 1.0), (15, 0.7), (25, 0.4)],
    roe_thresholds=_ROE_THRESHOLDS,
    dividend_thresholds=[(0.04, 1.0), (0.03, 0.7), (0.02, 0.4)],
    growth_thresholds=[(0.20, 1.0), (0.10, 0.7), (0.00, 0.4)],
)

INCOME_PROFILE = ScoringProfile(
    name="インカム型",
    fundamental_split=0.70,
    per_weight=0.15, pbr_weight=0.25, roe_weight=0.15,
    dividend_weight=0.40, growth_weight=0.05,
    per_thresholds=[(10, 1.0), (12, 0.7), (18, 0.4)],
    roe_thresholds=_ROE_THRESHOLDS,
    dividend_thresholds=[(0.05, 1.0), (0.04, 0.7), (0.03, 0.4)],
    growth_thresholds=[(0.10, 1.0), (0.05, 0.7), (0.00, 0.4)],
)


PROFILES = {
    "growth": GROWTH_PROFILE,
    "balanced": BALANCED_PROFILE,
    "income": INCOME_PROFILE,
}


def get_profile(key: str) -> ScoringProfile:
    """profile key (growth|balanced|income) からプロファイルを返す。"""
    return PROFILES.get(key, BALANCED_PROFILE)


def compute_phase_score(stock: Any, profile: ScoringProfile) -> float:
    """プロファイルに基づき phase_score (0〜100) を計算する。

    stock は per/pbr/roe/dividend_yield/revenue_growth/ma_score/rsi_score/macd_score
    属性を持つオブジェクト（StockScore ORM でも dict でも動くよう getattr を使う）。
    """
    def _g(key):
        if isinstance(stock, dict):
            return stock.get(key)
        return getattr(stock, key, None)

    f_raw = (
        _normalize_max(_g("per"), profile.per_thresholds) * profile.per_weight +
        _normalize_pbr(_g("pbr")) * profile.pbr_weight +
        _normalize_min(_g("roe"), profile.roe_thresholds) * profile.roe_weight +
        _normalize_min(_g("dividend_yield"), profile.dividend_thresholds) * profile.dividend_weight +
        _normalize_min(_g("revenue_growth"), profile.growth_thresholds) * profile.growth_weight
    )
    f_score = f_raw * profile.fundamental_split * 100

    t_raw = (
        (_g("ma_score") or 0) / 20.0 +
        (_g("rsi_score") or 0) / 15.0 +
        (_g("macd_score") or 0) / 15.0
    ) / 3.0
    t_score = t_raw * (1.0 - profile.fundamental_split) * 100

    return round(f_score + t_score, 2)
