"""黒点子スクリーナー - stock-advisor/analyzer/kurotenko_screener.py から移植
DB依存（StockMaster lookup）を除去し、純粋な yfinance ベースの評価のみ残す。
"""
from __future__ import annotations

from typing import Optional

import pandas as pd


def _is_valid(v):
    if v is None:
        return False
    try:
        return not pd.isna(v)
    except (TypeError, ValueError):
        return True


_OP_INCOME_KEYS = ["Operating Income", "EBIT", "Net Income"]
_REVENUE_KEYS = ["Total Revenue", "Revenue"]


def _find_row(df, keys):
    if df is None:
        return None
    for k in keys:
        if k in df.index:
            return df.loc[k]
    return None


try:
    from curl_cffi import requests as _cffi_requests
    _YF_SESSION = _cffi_requests.Session(impersonate="chrome")
except Exception:
    _YF_SESSION = None


def evaluate_candidate(symbol: str, interval_sec: float = 0) -> "Optional[dict]":
    """symbol に対して黒点子の8条件を評価して返す。

    Returns:
        dict with keys: year_end_turnaround, consec_quarters_profit, sales_yoy,
                        equity_ratio, cf_positive, cash_over_debt, avg_volume,
                        market_cap, rating (int 0-8)
        None if yfinance raises an exception.
    """
    import yfinance as yf
    import time
    if interval_sec:
        time.sleep(interval_sec)
    try:
        ticker = yf.Ticker(symbol, session=_YF_SESSION)
        info = ticker.info or {}
        fin = ticker.financials
        qfin = ticker.quarterly_income_stmt
        if qfin is None or (hasattr(qfin, 'empty') and qfin.empty):
            qfin = ticker.quarterly_financials
        bs = ticker.balance_sheet
        cf = ticker.cashflow

        # 1. Year-end turnaround
        year_end_turnaround = None
        if fin is not None and "Operating Income" in fin.index and fin.shape[1] >= 2:
            prev = fin.loc["Operating Income"].iloc[1]
            curr = fin.loc["Operating Income"].iloc[0]
            if _is_valid(prev) and _is_valid(curr):
                year_end_turnaround = bool(prev < 0 and curr > 0)

        # 2. Consecutive quarterly profit
        consec_quarters_profit = None
        op_row = _find_row(qfin, _OP_INCOME_KEYS)
        if op_row is not None and len(op_row) >= 2:
            q0 = op_row.iloc[0]
            q1 = op_row.iloc[1]
            if _is_valid(q0) and _is_valid(q1):
                consec_quarters_profit = bool(q0 > 0 and q1 > 0)

        # 3. Sales YoY growth
        sales_yoy = None
        rev_row = _find_row(fin, _REVENUE_KEYS)
        if rev_row is not None and len(rev_row) >= 2:
            r_prev = rev_row.iloc[1]
            r_curr = rev_row.iloc[0]
            if _is_valid(r_prev) and _is_valid(r_curr) and r_prev > 0:
                sales_yoy = bool(r_curr > r_prev)

        # 4. Equity ratio >= 30%
        equity_ratio = None
        if bs is not None and "Total Stockholder Equity" in bs.index and "Total Assets" in bs.index:
            eq = bs.loc["Total Stockholder Equity"].iloc[0]
            ta_val = bs.loc["Total Assets"].iloc[0]
            if _is_valid(eq) and _is_valid(ta_val) and ta_val > 0:
                equity_ratio = bool((eq / ta_val) >= 0.30)

        # 5. Operating cash flow positive
        cf_positive = None
        if cf is not None and "Operating Cash Flow" in cf.index and cf.shape[1] >= 1:
            val = cf.loc["Operating Cash Flow"].iloc[0]
            if _is_valid(val):
                cf_positive = bool(val > 0)

        # 6. Cash > total debt
        cash_over_debt = None
        if bs is not None:
            cash_keys = ["Cash And Cash Equivalents", "Cash"]
            debt_keys = ["Total Debt", "Long Term Debt"]
            cash_row = _find_row(bs, cash_keys)
            debt_row = _find_row(bs, debt_keys)
            if cash_row is not None and debt_row is not None:
                cash_val = cash_row.iloc[0]
                debt_val = debt_row.iloc[0]
                if _is_valid(cash_val) and _is_valid(debt_val):
                    cash_over_debt = bool(cash_val > debt_val)

        # 7. Average volume >= 100,000
        avg_volume = None
        avg_vol = info.get("averageVolume")
        if avg_vol is not None:
            avg_volume = bool(avg_vol >= 100_000)

        # 8. Market cap >= 10B JPY
        market_cap = None
        mc = info.get("marketCap")
        if mc is not None:
            market_cap = bool(mc >= 10_000_000_000)

        bool_criteria = [
            year_end_turnaround, consec_quarters_profit, sales_yoy,
            equity_ratio, cf_positive, cash_over_debt, avg_volume, market_cap,
        ]
        rating = sum(1 for v in bool_criteria if v is True)

        return {
            "year_end_turnaround": year_end_turnaround,
            "consec_quarters_profit": consec_quarters_profit,
            "sales_yoy": sales_yoy,
            "equity_ratio": equity_ratio,
            "cf_positive": cf_positive,
            "cash_over_debt": cash_over_debt,
            "avg_volume": avg_volume,
            "market_cap": market_cap,
            "rating": rating,
        }
    except Exception:
        import logging
        logging.getLogger(__name__).exception("%s: evaluate_candidate 失敗", symbol)
        return None
