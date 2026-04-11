"""tradingview-ta 同期ラッパー

非公式 tradingview-ta ライブラリを使って TradingView の指標・推奨を取得する。
yfinance との互換性のため、info は yfinance.ticker.info と同じキー名にマッピングする。

MCP は Claude からしか呼べないため、バックエンドの自動バッチはこのクライアントを使う。
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# シンボル変換: "7203.T" -> ("TSE", "7203")
# kabu-trade は JPX を前提にしているので exchange は固定で問題ない。
_JPX_EXCHANGE = "TSE"
_SCREENER = "japan"


def symbol_to_tv(symbol: str) -> Optional[tuple[str, str]]:
    """`7203.T` → `(TSE, 7203)` 形式に変換する。未知形式は None。"""
    if not symbol:
        return None
    code = symbol.split(".")[0].strip()
    if not code or not code.isalnum():
        return None
    return _JPX_EXCHANGE, code


def _to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _map_indicators_to_info(indicators: dict) -> dict:
    """tradingview-ta の indicators dict を yfinance.ticker.info 互換キーにマップする。

    tradingview-ta の key 命名は TradingView の scan API 準拠。利用可能性はシンボル毎に
    変わるため、取れたものだけ埋める（None は呼び出し側で yfinance フォールバック）。
    """
    get = indicators.get

    trailing_pe = _to_float(get("price_earnings_ttm"))
    price_to_book = _to_float(get("price_book_fq") or get("price_book_ratio"))
    roe_raw = _to_float(get("return_on_equity") or get("return_on_equity_fq"))
    # tradingview-ta は ROE を % 単位で返すことがあるので 1 より大きければ百分率と解釈。
    if roe_raw is not None and abs(roe_raw) > 1.5:
        roe_raw = roe_raw / 100.0
    dividend_yield = _to_float(get("dividend_yield_current") or get("dividends_yield"))
    if dividend_yield is not None and dividend_yield > 1.0:
        dividend_yield = dividend_yield / 100.0

    return {
        "trailingPE": trailing_pe,
        "priceToBook": price_to_book,
        "returnOnEquity": roe_raw,
        "dividendYield": dividend_yield,
    }


def fetch_stock_data_tv(symbol: str) -> Optional[dict]:
    """TradingView から指標・推奨を取得する。

    Returns:
        {
          "symbol": str,
          "info": {yfinance 互換 key: value, ...},  # 欠損は None
          "recommendation": "STRONG_BUY" | "BUY" | "NEUTRAL" | "SELL" | "STRONG_SELL" | None,
          "tv_indicators": dict,  # 生の indicators
        }
        取得失敗時は None。
    """
    try:
        from tradingview_ta import TA_Handler, Interval
    except ImportError:
        logger.error("tradingview_ta が未インストール: requirements.txt に追加してください")
        return None

    pair = symbol_to_tv(symbol)
    if pair is None:
        logger.warning("%s: TV 用シンボル変換に失敗", symbol)
        return None
    exchange, code = pair

    try:
        handler = TA_Handler(
            symbol=code,
            exchange=exchange,
            screener=_SCREENER,
            interval=Interval.INTERVAL_1_DAY,
            timeout=10,
        )
        analysis = handler.get_analysis()
    except Exception as e:
        logger.warning("%s: tradingview-ta 取得失敗 - %s", symbol, e)
        return None

    indicators = analysis.indicators or {}
    summary = analysis.summary or {}

    info = _map_indicators_to_info(indicators)
    return {
        "symbol": symbol,
        "info": info,
        "recommendation": summary.get("RECOMMENDATION"),
        "tv_indicators": indicators,
    }


def merge_info(base: dict, override: dict) -> dict:
    """yfinance の info に tradingview-ta 由来の値を上書きする。

    override 側に None が入っていても base の値を潰さない（欠損は埋めない）。
    """
    merged = dict(base or {})
    for k, v in (override or {}).items():
        if v is not None:
            merged[k] = v
    return merged
