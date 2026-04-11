"""ライフステージ phase scorer - stock-advisor/portfolio/phase_scorer.py から移植

目標額に対する進捗率で投資フェーズを決め、プロファイル選択とボーナス計算に使う。
- 0-30%   : 積立期   → 成長型プロファイル + ハイリスク指標にボーナス
- 30-70%  : 成長期   → バランス型プロファイル + ボーナスなし
- 70%+    : 安定期   → インカム型プロファイル + 配当/PBR にボーナス
"""

from typing import Any

_PHASE_WEIGHTS = {
    "積立期": {
        "revenue_growth_bonus": 3,
        "roe_bonus": 2,
        "dividend_bonus": -2,
        "pbr_bonus": 0,
        "technical_bonus": 2,
    },
    "成長期": {
        "revenue_growth_bonus": 0,
        "roe_bonus": 0,
        "dividend_bonus": 0,
        "pbr_bonus": 0,
        "technical_bonus": 0,
    },
    "安定期": {
        "revenue_growth_bonus": -2,
        "roe_bonus": 0,
        "dividend_bonus": 3,
        "pbr_bonus": 2,
        "technical_bonus": -1,
    },
}

_BONUS_FIELD_MAP = {
    "revenue_growth_bonus": "revenue_growth",
    "roe_bonus": "roe",
    "dividend_bonus": "dividend_yield",
    "pbr_bonus": "pbr",
    "technical_bonus": "technical_score",
}


def get_phase(progress_rate: float) -> str:
    """進捗率 (%) → '積立期' | '成長期' | '安定期'"""
    if progress_rate < 30:
        return "積立期"
    if progress_rate < 70:
        return "成長期"
    return "安定期"


def get_score_weights(phase: str) -> dict:
    return dict(_PHASE_WEIGHTS[phase])


def apply_phase_weights(score_dict: dict, weights: dict) -> dict:
    """adjusted_total_score を追加した新しい dict を返す（元は変更しない）。

    ボーナスは対応フィールドが None でない場合のみ加算。adjusted は [0, 100] にクランプ。
    """
    bonus = sum(
        weights.get(bonus_key, 0)
        for bonus_key, field in _BONUS_FIELD_MAP.items()
        if score_dict.get(field) is not None
    )
    adjusted = max(0.0, min(100.0, (score_dict.get("total_score") or 0) + bonus))
    return {**score_dict, "adjusted_total_score": adjusted}


def profile_for_phase(phase: str):
    """phase → ScoringProfile の対応表。循環 import 回避のため関数内 import。"""
    from app.analyzer.scoring_profiles import GROWTH_PROFILE, BALANCED_PROFILE, INCOME_PROFILE
    return {
        "積立期": GROWTH_PROFILE,
        "成長期": BALANCED_PROFILE,
        "安定期": INCOME_PROFILE,
    }[phase]


def score_to_dict(score: Any) -> dict:
    """StockScore ORM → apply_phase_weights 用 dict に変換"""
    return {
        "total_score": getattr(score, "total_score", None) or 0,
        "revenue_growth": getattr(score, "revenue_growth", None),
        "roe": getattr(score, "roe", None),
        "dividend_yield": getattr(score, "dividend_yield", None),
        "pbr": getattr(score, "pbr", None),
        "technical_score": getattr(score, "technical_score", None),
    }
