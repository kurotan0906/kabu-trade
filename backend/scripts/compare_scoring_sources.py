"""hybrid vs screener スコア比較ツール。

Usage:
    cd backend && PYTHONPATH=. .venv/bin/python3.11 scripts/compare_scoring_sources.py --limit 100

出力: backend/scoring_diff.csv + 集計サマリ（mean/median/abs_max/rating一致率）
"""
from __future__ import annotations

import argparse
import csv
import statistics
from typing import Optional

from app.analyzer.fundamental import calc_fundamental_score
from app.analyzer.scorer import build_stock_result, get_rating
from app.analyzer.technical import calc_technical_score
from app.analyzer.technical_from_tv import calc_technical_score_from_tv
from app.external.tv_screener_adapter import tv_row_to_info, tv_row_to_technical_features
from app.external.tv_screener_client import fetch_japan_market_snapshot
from app.external.yfinance_client import fetch_stock_data, load_jpx_symbols


def score_hybrid(symbol: str) -> Optional[dict]:
    """現行 hybrid パス（yfinance history + info）でスコアを計算。"""
    data = fetch_stock_data(symbol)
    if data is None or data.get("history") is None:
        return None
    info = data.get("info") or {}
    fund = calc_fundamental_score(info)
    tech = calc_technical_score(data["history"])
    result = build_stock_result(symbol, None, None, fund, tech, None)
    return result


def score_screener(symbol: str, snapshot: dict) -> Optional[dict]:
    """新 screener パス（TV 断面値のみ）でスコアを計算。"""
    row = snapshot.get(symbol)
    if row is None:
        return None
    info = tv_row_to_info(row)
    feats = tv_row_to_technical_features(row)
    fund = calc_fundamental_score(info)
    tech = calc_technical_score_from_tv(feats)
    result = build_stock_result(symbol, None, None, fund, tech, None)
    return result


def main(limit: int):
    print(f"TV Screener snapshot 取得中...")
    snapshot = fetch_japan_market_snapshot()
    print(f"  snapshot n={len(snapshot)}")

    symbols_data = load_jpx_symbols()
    # JPX 上位 limit 件（先頭取り）
    symbols = [row["symbol"] for row in symbols_data[:limit]]
    print(f"比較対象銘柄数={len(symbols)}")

    rows = []
    hybrid_fail = 0
    screener_fail = 0
    for i, s in enumerate(symbols):
        try:
            h = score_hybrid(s)
        except Exception as e:
            print(f"  [{i+1}/{len(symbols)}] {s} hybrid error: {e}")
            h = None
        try:
            sc = score_screener(s, snapshot)
        except Exception as e:
            print(f"  [{i+1}/{len(symbols)}] {s} screener error: {e}")
            sc = None

        if h is None:
            hybrid_fail += 1
        if sc is None:
            screener_fail += 1

        if h is not None and sc is not None:
            rows.append({
                "symbol": s,
                "hybrid_total": h["total_score"],
                "screener_total": sc["total_score"],
                "total_diff": sc["total_score"] - h["total_score"],
                "hybrid_fund": h["fundamental_score"],
                "screener_fund": sc["fundamental_score"],
                "fund_diff": sc["fundamental_score"] - h["fundamental_score"],
                "hybrid_tech": h["technical_score"],
                "screener_tech": sc["technical_score"],
                "tech_diff": sc["technical_score"] - h["technical_score"],
                "hybrid_rating": h["rating"],
                "screener_rating": sc["rating"],
                "rating_match": h["rating"] == sc["rating"],
            })
        if (i + 1) % 10 == 0:
            print(f"  進捗 {i+1}/{len(symbols)} pair_ok={len(rows)} hybrid_fail={hybrid_fail} screener_fail={screener_fail}")

    out_path = "scoring_diff.csv"
    with open(out_path, "w", newline="") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print(f"\nCSV 出力: {out_path}")

    if not rows:
        print("比較可能なペアが 0 件。")
        return

    total_diffs = [r["total_diff"] for r in rows]
    fund_diffs = [r["fund_diff"] for r in rows]
    tech_diffs = [r["tech_diff"] for r in rows]
    rating_matches = sum(1 for r in rows if r["rating_match"])

    print("\n=== 集計サマリ ===")
    print(f"比較ペア数: {len(rows)}")
    print(f"hybrid 失敗: {hybrid_fail} / screener 失敗: {screener_fail}")
    print()
    print(f"total_score 差分:  mean={statistics.mean(total_diffs):+.2f}  median={statistics.median(total_diffs):+.2f}  abs_max={max(abs(d) for d in total_diffs):.2f}")
    print(f"fundamental 差分:  mean={statistics.mean(fund_diffs):+.2f}  median={statistics.median(fund_diffs):+.2f}  abs_max={max(abs(d) for d in fund_diffs):.2f}")
    print(f"technical 差分:    mean={statistics.mean(tech_diffs):+.2f}  median={statistics.median(tech_diffs):+.2f}  abs_max={max(abs(d) for d in tech_diffs):.2f}")
    print(f"rating 一致率:     {rating_matches}/{len(rows)} = {rating_matches/len(rows)*100:.1f}%")
    print()
    print("合格ライン:  mean_abs ≤ 3 pt / rating一致率 ≥ 95% / abs_max ≤ 10 pt")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=100, help="比較対象銘柄数（JPX 先頭から）")
    args = p.parse_args()
    main(args.limit)
