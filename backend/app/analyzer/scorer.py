"""総合スコア・レーティング計算 - stock-advisor/analyzer/scorer.py から移植"""
from __future__ import annotations

from typing import Optional


def get_rating(score: float) -> str:
    if score >= 80:
        return "強い買い"
    if score >= 60:
        return "買い"
    if score >= 40:
        return "中立"
    if score >= 20:
        return "売り"
    return "強い売り"


def build_stock_result(
    symbol: str,
    name: Optional[str],
    sector: Optional[str],
    fundamental: dict,
    technical: dict,
    kurotenko: Optional[dict] = None,
) -> dict:
    """各スコアを統合して stock_scores レコード用の dict を返す。"""
    total = fundamental["fundamental_score"] + technical["technical_score"]

    kurotenko_score = None
    kurotenko_criteria = None
    if kurotenko is not None:
        criteria_met = kurotenko["rating"]  # 0-8
        kurotenko_score = (criteria_met / 8) * 100
        kurotenko_criteria = {
            k: v for k, v in kurotenko.items() if k != "rating"
        }

    return {
        "symbol": symbol,
        "name": name,
        "sector": sector,
        "total_score": total,
        "rating": get_rating(total),
        "fundamental_score": fundamental["fundamental_score"],
        "technical_score": technical["technical_score"],
        "kurotenko_score": kurotenko_score,
        "kurotenko_criteria": kurotenko_criteria,
        "per": fundamental.get("per"),
        "pbr": fundamental.get("pbr"),
        "roe": fundamental.get("roe"),
        "dividend_yield": fundamental.get("dividend_yield"),
        "revenue_growth": fundamental.get("revenue_growth"),
        "ma_score": technical.get("ma_score"),
        "rsi_score": technical.get("rsi_score"),
        "macd_score": technical.get("macd_score"),
        "data_quality": fundamental.get("data_quality", "ok"),
    }
