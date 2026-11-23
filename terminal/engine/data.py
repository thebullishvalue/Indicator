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

# The watchlist, in the sections and order of the user's TradingView list:
# (display, Yahoo ticker, exchange, description, section, decimals shown).
# Yahoo serves no GIFT Nifty (NIFTY1!), no MCX contracts (GOLD1!, SILVER1!) and no spot gold or silver, so those are
# left out and COMEX's front-month futures stand in for TradingView's spot GOLD and SILVER.
WATCHLIST = [
    ("NIFTY", "^NSEI", "NSE", "Nifty 50 Index", "India", 2),
    ("SENSEX", "^BSESN", "BSE", "S&P BSE Sensex Index", "India", 2),
    ("BANKNIFTY", "^NSEBANK", "NSE", "Nifty Bank Index", "India", 2),
    ("CNXMIDCAP", "NIFTY_MIDCAP_100.NS", "NSE", "Nifty Midcap 100 Index", "India", 2),
    ("CNXSMALLCAP", "^CNXSC", "NSE", "Nifty Smallcap 100 Index", "India", 2),
    ("NIFTY_MICROCAP250", "NIFTY_MICROCAP250.NS", "NSE", "Nifty Microcap 250 Index", "India", 2),
    ("INDIAVIX", "^INDIAVIX", "NSE", "India VIX Index", "India", 4),
    ("USDINR", "INR=X", "FX", "U.S. Dollar / Indian Rupee", "India", 4),
    ("ES1!", "ES=F", "CME", "E-mini S&P 500 Futures", "United States", 2),
    ("US10Y", "^TNX", "TVC", "US Government Bonds 10 YR Yield", "United States", 3),
    ("DXY", "DX-Y.NYB", "ICE", "U.S. Dollar Index", "United States", 3),
    ("CT2!", "CT=F", "ICE", "Cotton No. 2 Futures", "Commodities", 2),
    ("GOLD", "GC=F", "COMEX", "Gold · COMEX futures", "Commodities", 2),
    ("SILVER", "SI=F", "COMEX", "Silver · COMEX futures", "Commodities", 3),
    ("USOIL", "CL=F", "NYMEX", "WTI Crude Oil · NYMEX futures", "Commodities", 2),
    ("UKOIL", "BZ=F", "ICE", "Brent Crude Oil · ICE futures", "Commodities", 2),
    ("BTCUSD", "BTC-USD", "CRYPTO", "Bitcoin / U.S. Dollar", "Crypto", 2),
]
SECTIONS = ["India", "United States", "Commodities", "Crypto"]

# TradingView symbols Yahoo does not carry, and what to open instead.
UNAVAILABLE = {
    "NIFTY1!": "GIFT Nifty futures are not on Yahoo. NIFTY, the cash index, is.",
    "BANKNIFTY1!": "NSE futures are not on Yahoo. BANKNIFTY, the cash index, is.",
    "GOLD1!": "MCX contracts are not on Yahoo. GOLD (COMEX gold futures) is the nearest.",
    "SILVER1!": "MCX contracts are not on Yahoo. SILVER (COMEX silver futures) is the nearest.",
    "CRUDEOIL1!": "MCX contracts are not on Yahoo. USOIL (NYMEX WTI futures) is the nearest.",
    "XAUUSD": "Spot gold is not on Yahoo. GOLD (COMEX gold futures) is the nearest.",
    "XAGUSD": "Spot silver is not on Yahoo. SILVER (COMEX silver futures) is the nearest.",
}


def hint(symbol: str) -> str:
    """Why a symbol has no data, when it is one we know about, else how to type one."""
    s = symbol.strip().upper().split(":")[-1]
    return UNAVAILABLE.get(s, "Try a watchlist name (NIFTY, GOLD), NSE:TCS for an NSE stock, or a Yahoo ticker (AAPL, GC=F, BTC-USD).")


def resolve(symbol: str) -> tuple[str, str, str, str]:
    """A typed symbol to (display, Yahoo ticker, exchange, description). Accepts watchlist names, 'NSE:XYZ' and Yahoo tickers."""
    s = symbol.strip()
    for row in WATCHLIST:
        if s.upper() in (row[0], row[1].upper()):
            return row[:4]
    if ":" in s:
        ex, tk = s.split(":", 1)
        ex, tk = ex.upper(), tk.upper()
        for row in WATCHLIST:              # TradingView's prefixed names: NSE:NIFTY, TVC:GOLD, CME_MINI:ES1!
            if tk == row[0]:
                return row[:4]
        if ex == "NSE":
            return tk, f"{tk}.NS", "NSE", tk
        if ex == "BSE":
            return tk, f"{tk}.BO", "BSE", tk
        return tk, tk, ex, tk
    return s.upper(), s.upper(), "", s.upper()


def fetch(ticker: str, tf: Timeframe) -> tuple[pd.DataFrame, dict]:
    """Bars for the chart: open/high/low/close/volume, oldest first, plus Yahoo's metadata (price hint, exchange, tz).

    Daily bars come from `daily()`, which repairs what Yahoo's daily series misses; weekly and monthly bars are rolled
    up from them (Monday weeks, calendar months), as TradingView builds its own."""
    import yfinance as yf
    if tf.yf in ("1wk", "1mo"):
        d, meta = daily(ticker)
        return _rollup(d, tf.yf), meta
    if tf.yf == "1d":
        return daily(ticker)
    t = yf.Ticker(ticker)
    df = _clean(t.history(period=tf.period, interval=tf.yf, auto_adjust=False, actions=False))
    meta = _meta(t)
    if tf.resample and len(df):
        df = _resample(df, tf.resample)
    return df, meta


def daily(ticker: str, period: str = "max") -> tuple[pd.DataFrame, dict]:
    """Daily bars, with two of Yahoo's gaps repaired from its hourly bars. meta gains builtFrom / patched when they apply.

    1. Some NSE indices (Midcap 100, Smallcap 100, Microcap 250) carry a single daily bar but about three years of
       hourly bars: their daily bars are built from those (closes match Yahoo's own daily closes exactly, highs and
       lows to a few hundredths of a percent).
    2. Yahoo's daily series for NSE and BSE indices runs a session behind: on 23 Nov 2026 NIFTY's last daily bar was
       20 Nov while its hourly bars and quote had 23 Nov. Sessions after the last daily bar, up to the date Yahoo's own
       market time gives, are built from the hourly bars, and the last one closes at the official close
       (regularMarketPrice). Futures and crypto, whose daily bars are current, are left as they are.
    """
    import yfinance as yf
    t = yf.Ticker(ticker)
    df = _clean(t.history(period=period, interval="1d", auto_adjust=False, actions=False))
    meta = _meta(t)
    short = len(df) < (60 if period == "max" else 3)
    try:      # secondary: a fund has daily bars only, and yfinance raises on its hourly request
        hourly = _clean(t.history(period="730d" if short and period == "max" else "5d", interval="60m", auto_adjust=False, actions=False))
    except Exception:
        hourly = _clean(None)
    if short:
        built = _rollup(hourly, "1d")
        if len(built) > len(df):
            df, meta["builtFrom"] = built, "60m"
        return df, meta
    rmt, rmp = meta.get("regularMarketTime"), meta.get("regularMarketPrice")
    if not len(df) or not len(hourly) or rmt is None:
        return df, meta
    try:
        mkt_day = pd.Timestamp(rmt).tz_convert(df.index.tz).normalize() if df.index.tz is not None else pd.Timestamp(rmt).normalize()
    except Exception:
        return df, meta
    last_day = df.index[-1].normalize()
    if mkt_day <= last_day:
        return df, meta
    hd = _rollup(hourly, "1d")
    hd = hd[(hd.index > last_day) & (hd.index <= mkt_day)]
    if not len(hd):
        return df, meta
    if isinstance(rmp, (int, float)) and rmp > 0 and hd.index[-1] == mkt_day:
        i = hd.index[-1]
        hd.loc[i, "close"] = float(rmp)
        hd.loc[i, "high"] = max(hd.loc[i, "high"], float(rmp))
        hd.loc[i, "low"] = min(hd.loc[i, "low"], float(rmp))
    meta["patched"] = dict(after=last_day, sessions=[d for d in hd.index])
    return pd.concat([df, hd]).sort_index(), meta


def _meta(t) -> dict:
    """Yahoo's metadata for the last request. yfinance's lazy mapping raises on fields some symbols lack (a fund has no
    tradingPeriods), so it is read field by field."""
    m = getattr(t, "history_metadata", None) or {}
    try:
        return dict(m)
    except Exception:
        out = {}
        for k in list(getattr(m, "keys", lambda: [])()):
            try:
                out[k] = m[k]
            except Exception:
                pass
        return out


def _rollup(h: pd.DataFrame, interval: str) -> pd.DataFrame:
    """Daily, weekly (Monday) or monthly bars from finer ones, on the exchange's calendar."""
    if not len(h):
        return h
    day = h.index.normalize()
    key = day if interval == "1d" else day - pd.to_timedelta(day.weekday, "D") if interval == "1wk" else day - pd.to_timedelta(day.day - 1, "D")
    g = h.groupby(key)
    out = pd.DataFrame(dict(open=g.open.first(), high=g.high.max(), low=g.low.min(), close=g.close.last(), volume=g.volume.sum()))
    out.index.name = None
    return out.dropna(subset=["close"])


def quote(ticker: str) -> tuple[float, float, float] | None:
    """(last, change, change %) off the same repaired daily bars the chart draws, so the watchlist and chart agree."""
    try:
        d, _ = daily(ticker, "1mo")
    except Exception:
        return None
    if len(d) < 2:
        return None
    c = d.close
    return float(c.iloc[-1]), float(c.iloc[-1] - c.iloc[-2]), float(c.iloc[-1] / c.iloc[-2] - 1) * 100


# Which of the toolbar's intervals Yahoo has for a symbol: one short request per intraday resolution.
_PROBE = {"1m": "1m", "5m": "5m", "15m": "5m", "30m": "5m", "1h": "60m", "4h": "60m"}
_RES_NAME = {"1m": "1-minute", "5m": "5-minute", "60m": "hourly"}


def availability(ticker: str) -> dict[str, str]:
    """{interval: ""} where Yahoo has bars, {interval: reason} where it has none. All empty-handed: an unknown symbol."""
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor

    def probe(res: str) -> int:
        try:
            if res == "1d":
                return len(quote(ticker) or ())
            return len(_clean(yf.Ticker(ticker).history(period="5d", interval=res, auto_adjust=False, actions=False)))
        except Exception:
            return 0
    with ThreadPoolExecutor(4) as ex:
        got = dict(zip(["1d", "1m", "5m", "60m"], ex.map(probe, ["1d", "1m", "5m", "60m"])))
    out = {}
    for k in TIMEFRAMES:
        res = _PROBE.get(k, "1d")
        out[k] = "" if got[res] else (f"Yahoo has no {_RES_NAME[res]} bars for {ticker}" if res != "1d" else f"Yahoo has no bars for {ticker}")
    return out


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
    df = df[df.close > 0]
    # Yahoo carries the odd zero open, high or low (CT=F, the week of 25 May 2020, has a low of 0), whose log is minus
    # infinity and would end the risk forecast for good. A zero price is a missing one: open falls back to the close,
    # high and low to the larger and smaller of open and close.
    df = df.assign(open=df.open.where(df.open > 0, df.close))
    df = df.assign(high=df.high.where(df.high > 0, df[["open", "close"]].max(axis=1)),
                   low=df.low.where(df.low > 0, df[["open", "close"]].min(axis=1)))
    df = df[df.high >= df.low]
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df


def _resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    g = df.resample(rule, origin="start_day", label="left", closed="left")
    out = pd.DataFrame(dict(open=g.open.first(), high=g.high.max(), low=g.low.min(), close=g.close.last(), volume=g.volume.sum()))
    return out.dropna(subset=["close"])
