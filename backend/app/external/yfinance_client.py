"""yfinance 同期ラッパー - バッチスコアリング専用

yfinance は同期ライブラリ。async 環境からは run_in_executor 経由で呼ぶこと。
"""

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
RETRY_SLEEP = 1.0

try:
    from curl_cffi import requests as _cffi_requests
    _YF_SESSION = _cffi_requests.Session(impersonate="chrome")
    logger.info("yfinance_client: curl-cffi セッションを使用")
except Exception:
    _YF_SESSION = None


def fetch_stock_data(symbol: str) -> Optional[dict]:
    """symbol の yfinance データを取得して返す。失敗時は None。

    Returns:
        {"symbol": str, "history": pd.DataFrame, "info": dict} or None
    """
    import yfinance as yf

    for attempt in range(MAX_RETRIES + 1):
        try:
            ticker = yf.Ticker(symbol, session=_YF_SESSION)
            history = ticker.history(period="1y")
            if history.empty:
                logger.warning("%s: 履歴データが空", symbol)
                return None
            return {"symbol": symbol, "history": history, "info": ticker.info or {}}
        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning("%s: 取得失敗 (%d/%d) - %s", symbol, attempt + 1, MAX_RETRIES + 1, e)
                time.sleep(RETRY_SLEEP)
            else:
                logger.error("%s: 取得断念 - %s", symbol, e)
                return None


def load_jpx_symbols() -> list:
    """JPX 銘柄マスター Excel をダウンロードして銘柄リストを返す。

    Returns:
        [{"symbol": "7203.T", "name": "トヨタ自動車", "market": "プライム（内国株式）"}, ...]
    """
    import io
    import requests
    import pandas as pd

    JPX_EXCEL_URL = (
        "https://www.jpx.co.jp/markets/statistics-equities/misc/"
        "tvdivq0000001vg2-att/data_j.xls"
    )
    resp = requests.get(JPX_EXCEL_URL, timeout=30)
    resp.raise_for_status()
    df = pd.read_excel(io.BytesIO(resp.content), dtype=str)
    rows = []
    for _, row in df.iterrows():
        code = str(row.get("コード", "")).strip()
        name = str(row.get("銘柄名", "")).strip()
        market = str(row.get("市場・商品区分", "")).strip()
        if not code or code == "nan":
            continue
        rows.append({"symbol": f"{code}.T", "name": name, "market": market})
    return rows
