"""将来価値シミュレータ - stock-advisor/portfolio/advisor_logic.py から移植

- _fv: 将来価値 = pv*(1+r)^n + mi*12*((1+r)^n-1)/r
- calculate_required_rate: 二分探索で必要年利を算出
- simulate: グラフ用の年次時系列を返す
"""

from typing import Optional


def future_value(pv: float, monthly_investment: float, annual_rate: float, years: float) -> float:
    """将来価値を計算する。rate=0 のケースも扱う。"""
    if years <= 0:
        return pv
    if annual_rate == 0:
        return pv + monthly_investment * 12 * years
    factor = (1 + annual_rate) ** years
    return pv * factor + monthly_investment * 12 * (factor - 1) / annual_rate


def calculate_required_rate(
    goal: float,
    pv: float,
    n_months: int,
    monthly_investment: float = 0.0,
) -> Optional[float]:
    """目標達成に必要な年利 (%) を返す。計算不能時は None。

    - 積立なしで pv>0: 指数から直接計算
    - 積立あり: 二分探索 ([-99%, +200%])
    - 既に積立のみで達成可能 → 0.0 を返す
    """
    if n_months <= 0 or pv <= 0:
        return None

    n_years = n_months / 12
    mi = monthly_investment

    if mi == 0:
        r = (goal / pv) ** (1 / n_years) - 1
        return round(r * 100, 2)

    if future_value(pv, mi, 0.0, n_years) >= goal:
        return 0.0

    lo, hi = -0.99, 2.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if future_value(pv, mi, mid, n_years) >= goal:
            hi = mid
        else:
            lo = mid
        if hi - lo < 1e-5:
            break
    return round(hi * 100, 2)


def simulate(pv: float, monthly_investment: float, annual_rate: float, years: int) -> list[dict]:
    """年次時系列 [{year: int, value: float, contributed: float, gain: float}, ...] を返す。

    value は future_value() による計算、contributed は累計拠出額。
    """
    if years <= 0:
        return []
    out = []
    total_contrib_initial = pv
    for y in range(0, years + 1):
        value = future_value(pv, monthly_investment, annual_rate, y)
        contributed = total_contrib_initial + monthly_investment * 12 * y
        out.append({
            "year": y,
            "value": round(value, 2),
            "contributed": round(contributed, 2),
            "gain": round(value - contributed, 2),
        })
    return out
