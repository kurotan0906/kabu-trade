"""ファンダメンタルスコア計算 - stock-advisor/analyzer/fundamental.py から移植"""


def score_per(value) -> int:
    if value is None:
        return 5
    if value <= 0:
        return 0
    if value <= 10:
        return 10
    if value <= 15:
        return 7
    if value <= 25:
        return 4
    return 0


def score_pbr(value) -> int:
    if value is None or value <= 0:
        return 5
    if value <= 0.8:
        return 10
    if value <= 1.0:
        return 7
    if value <= 1.5:
        return 4
    return 0


def score_roe(value) -> int:
    if value is None:
        return 5
    if value >= 0.20:
        return 10
    if value >= 0.15:
        return 7
    if value >= 0.10:
        return 4
    return 0


def score_dividend(value) -> int:
    if value is None:
        return 5
    if value >= 0.04:
        return 10
    if value >= 0.03:
        return 7
    if value >= 0.02:
        return 4
    return 0


def score_revenue_growth(value) -> int:
    if value is None:
        return 5
    if value >= 0.20:
        return 10
    if value >= 0.10:
        return 7
    if value >= 0.0:
        return 4
    return 0


def _to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calc_fundamental_score(info: dict) -> dict:
    """yfinance の ticker.info dict からファンダメンタルスコアを計算して返す。

    Returns:
        dict: fundamental_score (0-50), per, pbr, roe, dividend_yield, revenue_growth, data_quality
    """
    per = _to_float(info.get("trailingPE"))
    pbr = _to_float(info.get("priceToBook"))
    roe = _to_float(info.get("returnOnEquity"))
    div = _to_float(info.get("dividendYield"))
    rev = _to_float(info.get("revenueGrowth"))

    total = float(score_per(per) + score_pbr(pbr) + score_roe(roe) + score_dividend(div) + score_revenue_growth(rev))

    has_any = any(v is not None for v in [per, pbr, roe, div, rev])
    data_quality = "ok" if has_any else "partial"

    return {
        "fundamental_score": total,
        "per": per,
        "pbr": pbr,
        "roe": roe,
        "dividend_yield": div,
        "revenue_growth": rev,
        "data_quality": data_quality,
    }
