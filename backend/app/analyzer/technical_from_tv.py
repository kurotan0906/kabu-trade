"""TV Screener 指標値からテクニカルスコアを直接計算する（履歴不要版）。

現行 `calc_technical_score(history)` と同じ出力フォーマットを返すが、TV 断面値
を使うため pandas_ta / ta 再計算は行わない。

**現行ロジックとの差分**:
- `score_ma` / `score_rsi` は閾値が完全一致（TV の SMA25/SMA75/RSI を直接使用）
- `score_macd` は「直近3本でのクロス検出」が TV 断面で再現不可のため、
  非クロスケース（多数派）のスコアを採用:
    - macd > signal → +8 （現行: クロス無+上 = 8 / クロス有+上 = 15）
    - macd < signal → +3 （現行: クロス無+下 = 3 / クロス有+下 = 0）
    - None         → +3 （現行: default=3）
  トレードオフ: クロスタイミングのボーナス/ペナルティが消えるが、
  多数派（非クロス）の挙動を保存することで score 分布シフトを最小化。
"""
from __future__ import annotations

from typing import Any


def score_ma_from_tv(close: float | None, sma25: float | None, sma75: float | None) -> int:
    if close is None or sma25 is None or sma75 is None:
        return 6
    if close > sma25 and sma25 > sma75:
        return 20
    if close > sma25:
        return 12
    if close < sma25 and sma25 < sma75:
        return 0
    return 6


def score_rsi_from_tv(rsi: float | None) -> int:
    if rsi is None:
        return 8
    if rsi <= 30:
        return 15
    if rsi <= 39:
        return 10
    if rsi <= 60:
        return 8
    if rsi <= 69:
        return 4
    return 0


def score_macd_from_tv(macd: float | None, signal: float | None) -> int:
    """TV 断面では過去 N 本のクロス検出不可のため、非クロス側の値を採用。"""
    if macd is None or signal is None:
        return 3
    if macd > signal:
        return 8
    if macd < signal:
        return 3
    return 3


def calc_technical_score_from_tv(features: dict[str, Any]) -> dict[str, Any]:
    """TV 断面フィーチャーから technical_score を算出。

    Args:
        features: tv_screener_adapter.tv_row_to_technical_features の出力
    Returns:
        {technical_score (0-43), ma_score, rsi_score, macd_score}

        ※ 現行 calc_technical_score の最大値は 50 だが、本関数は MACD の
          クロスボーナスを落とすため実質最大 20+15+8=43。
          合計範囲が狭まる影響は Phase 1 差分検証で合格ライン確認する。
    """
    ma_s = score_ma_from_tv(features.get("close"), features.get("sma25"), features.get("sma75"))
    rsi_s = score_rsi_from_tv(features.get("rsi"))
    macd_s = score_macd_from_tv(features.get("macd"), features.get("macd_signal"))
    return {
        "technical_score": float(ma_s + rsi_s + macd_s),
        "ma_score": float(ma_s),
        "rsi_score": float(rsi_s),
        "macd_score": float(macd_s),
    }
