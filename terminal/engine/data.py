"""Market data for the terminal: bars from Yahoo Finance, the timeframes the chart offers, and the lower-timeframe
bars the volume profile spreads volume with.

Yahoo limits how far back intraday bars go (1m: 7 days; 2m-30m: 60 days; 1h: 730 days). The script's intrabar
timeframe is mapped to the nearest one Yahoo serves at or below it; bars older than Yahoo's intraday history fall
back to an even spread over the bar's range, exactly as the script does where intrabar data does not reach.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .profile import ltf_seconds, session_bars


@dataclass(frozen=True)
class Timeframe:
    label: str          # what the toolbar shows
    sec: int            # timeframe.in_seconds()
    yf: str             # Yahoo interval fetched
    period: str         # how far back Yahoo serves it
    resample: str | None = None


TIMEFRAMES = {
    "1m": Timeframe("1m", 60, "1m", "7d"),
    "5m": Timeframe("5m", 300, "5m", "60d"),
    "15m": Timeframe("15m", 900, "15m", "60d"),
    "30m": Timeframe("30m", 1800, "30m", "60d"),
    "1h": Timeframe("1h", 3600, "60m", "730d"),
    "4h": Timeframe("4h", 14400, "60m", "730d", resample="4h"),
    "D": Timeframe("D", 86400, "1d", "max"),
    "W": Timeframe("W", 604800, "1wk", "max"),
    "M": Timeframe("M", 2628000, "1mo", "max"),
}

# Pine intrabar seconds -> the Yahoo interval used for it (the nearest Yahoo serves, never coarser).
_LTF_YF = {60: ("1m", "7d", None), 120: ("2m", "60d", None), 180: ("2m", "60d", None), 300: ("5m", "60d", None),
           600: ("5m", "60d", None), 900: ("15m", "60d", None), 1800: ("30m", "60d", None), 3600: ("60m", "730d", None),
           7200: ("60m", "730d", "2h"), 14400: ("60m", "730d", "4h"), 86400: ("1d", "max", None)}
_PINE_LTF_NAME = {60: "1", 120: "2", 180: "3", 300: "5", 600: "10", 900: "15", 1800: "30", 3600: "60", 7200: "120",
                  14400: "240", 86400: "D"}

# A starting watchlist: (display, Yahoo ticker, exchange, description)
WATCHLIST = [
    ("NIFTY", "^NSEI", "NSE", "Nifty 50 Index"),
    ("BANKNIFTY", "^NSEBANK", "NSE", "Nifty Bank Index"),
    ("SPX", "^GSPC", "SP", "S&P 500 Index"),
    ("NDX", "^NDX", "NASDAQ", "Nasdaq 100 Index"),
    ("DXY", "DX-Y.NYB", "ICE", "US Dollar Index"),
    ("GOLD", "GC=F", "COMEX", "Gold Futures"),
    ("SILVER", "SI=F", "COMEX", "Silver Futures"),
    ("CRUDE", "CL=F", "NYMEX", "Crude Oil Futures"),
    ("BTCUSD", "BTC-USD", "CRYPTO", "Bitcoin / US Dollar"),
    ("ETHUSD", "ETH-USD", "CRYPTO", "Ethereum / US Dollar"),
    ("EURUSD", "EURUSD=X", "FX", "Euro / US Dollar"),
    ("USDINR", "INR=X", "FX", "US Dollar / Indian Rupee"),
    ("RELIANCE", "RELIANCE.NS", "NSE", "Reliance Industries"),
    ("HDFCBANK", "HDFCBANK.NS", "NSE", "HDFC Bank"),
    ("AAPL", "AAPL", "NASDAQ", "Apple Inc."),
    ("NVDA", "NVDA", "NASDAQ", "NVIDIA Corporation"),
]


def resolve(symbol: str) -> tuple[str, str, str, str]:
    """A typed symbol to (display, Yahoo ticker, exchange, description). Accepts watchlist names, 'NSE:XYZ' and Yahoo tickers."""
    s = symbol.strip()
    for row in WATCHLIST:
        if s.upper() in (row[0], row[1].upper()):
            return row
    if ":" in s:
        ex, tk = s.split(":", 1)
        ex, tk = ex.upper(), tk.upper()
        if ex == "NSE":
            return tk, f"{tk}.NS", "NSE", tk
        if ex == "BSE":
            return tk, f"{tk}.BO", "BSE", tk
        return tk, tk, ex, tk
    return s.upper(), s.upper(), "", s.upper()


def fetch(ticker: str, tf: Timeframe) -> tuple[pd.DataFrame, dict]:
    """Bars for the chart: open/high/low/close/volume, oldest first, plus Yahoo's metadata (price hint, exchange, tz)."""
    import yfinance as yf
    t = yf.Ticker(ticker)
    df = t.history(period=tf.period, interval=tf.yf, auto_adjust=False, actions=False)
    meta = dict(getattr(t, "history_metadata", {}) or {})
    df = _clean(df)
    if tf.resample and len(df):
        df = _resample(df, tf.resample)
    return df, meta


def fetch_intrabars(ticker: str, tf: Timeframe, chart: pd.DataFrame, inp_naked_age: int) -> tuple[dict, dict]:
    """The lower-timeframe bars inside each chart bar of the profile's stretch: {bar position: DataFrame}.

    Returns (intrabars, info) where info names the script's intrabar timeframe and the one Yahoo served.
    """
    ltf = ltf_seconds(tf.sec)
    info = dict(pine_ltf=_PINE_LTF_NAME.get(ltf) if ltf else None, yf_ltf=None, bars_with_intrabars=0)
    if ltf is None or not len(chart):
        return {}, info
    yf_int, period, res = _LTF_YF[ltf]
    info["yf_ltf"] = yf_int + (f"→{res}" if res else "")
    import yfinance as yf
    lo = yf.Ticker(ticker).history(period=period, interval=yf_int, auto_adjust=False, actions=False)
    lo = _clean(lo)
    if res and len(lo):
        lo = _resample(lo, res)
    if not len(lo):
        return {}, info
    n = len(chart)
    reach = 2 * inp_naked_age + 3 * session_bars(tf.sec)
    first = max(0, n - 1 - reach - session_bars(tf.sec))
    starts = chart.index.asi8
    ends = np.r_[starts[1:], starts[-1] + int(tf.sec * 1e9)]
    li = lo.index.asi8
    out = {}
    cvol = chart["volume"].to_numpy(float)
    refilled = 0
    for pos in range(first, n):
        a, b = np.searchsorted(li, starts[pos], "left"), np.searchsorted(li, ends[pos], "left")
        if b > a:
            ibars = lo.iloc[a:b]
            # Yahoo reports no intraday volume for some symbols (indices) whose daily bars carry it. TradingView's
            # intrabars carry the volume; here the bar's own volume is shared evenly over its intrabars instead.
            if not (ibars["volume"].fillna(0) > 0).any() and cvol[pos] > 0:
                ibars = ibars.assign(volume=cvol[pos] / len(ibars))
                refilled += 1
            out[pos] = ibars
    info["bars_with_intrabars"] = len(out)
    info["volume_refilled"] = refilled
    return out, info


def mintick_of(meta: dict, df: pd.DataFrame) -> float:
    """syminfo.mintick: Yahoo's price hint (decimal places), else read off the prices."""
    ph = meta.get("priceHint")
    if isinstance(ph, (int, float)) and ph >= 0:
        return 10.0 ** (-int(ph))
    px = float(np.nanmedian(df["close"])) if len(df) else 1.0
    return 10.0 ** (math.floor(math.log10(max(px, 1e-9))) - 4)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or not len(df):
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].astype(float)
    df = df[(df.close > 0) & (df.high >= df.low)]
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df


def _resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    g = df.resample(rule, origin="start_day", label="left", closed="left")
    out = pd.DataFrame(dict(open=g.open.first(), high=g.high.max(), low=g.low.min(), close=g.close.last(), volume=g.volume.sum()))
    return out.dropna(subset=["close"])
