"""
Anumaan - a terminal for anumaan.pine.
अनुमान (Anumāna) - "inference: knowing what cannot be seen from what can"

A chart terminal laid out the way a trading terminal is - symbol and interval on the toolbar, the chart with its
indicator pane, a watchlist and the symbol's details in the rail, the script's source, its proof, ledger,
calibration record, alert log and data window in the bottom panel - running anumaan.pine ported to Python bar for
bar, drawn on TradingView's open-source Lightweight Charts library.

    streamlit run terminal/app.py
"""
from __future__ import annotations

import html as H
import math
import sys
import warnings
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

st.set_page_config(page_title="Anumaan · Terminal", page_icon="◈", layout="wide", initial_sidebar_state="collapsed")

from engine import data as D, anumaan as P, profile as PR, table as TB  # noqa: E402
from engine.palette import palette  # noqa: E402
from ui import chart as C, components as K, inputs as I, panels as PN, theme  # noqa: E402

INTERVALS = list(D.TIMEFRAMES)
CHART_H = 760
# The rail is exactly as tall as the chart frame (CHART_H + its 1px borders), so the Symbol box's bottom is flush with
# the chart's. terminal.css fixes the numbers this adds up: a rail panel is 2px of border plus a 42px header, a key/value
# row is 30px, the rail's gap is 12px.
GAP, PANEL_CHROME, KV_ROW, SYMBOL_ROWS = 12, 2 + 42, 30, 3
WATCH_H = (CHART_H + 2) - GAP - (PANEL_CHROME + SYMBOL_ROWS * KV_ROW) - PANEL_CHROME

# ── state ──────────────────────────────────────────────────────────────────
ss = st.session_state
ss.setdefault("symbol", "NIFTY")
ss.setdefault("tf", "D")
ss.setdefault("appearance", "Slate")
ss.setdefault("volume", True)
ss.setdefault("inputs", P.Inputs().as_dict())
ss.setdefault("recent", [])
ss.setdefault("notes", [])          # events to tell the viewer about, shown as toasts on the next render
ss.setdefault("last_good", None)    # the last symbol that loaded, to fall back to when a new one has no data
if "booted" not in ss:              # a link or a reload opens the chart in the address bar: ?symbol=GOLD&tf=W
    ss.booted = True
    if st.query_params.get("symbol"):
        ss.symbol = st.query_params["symbol"]
    if st.query_params.get("tf") in D.TIMEFRAMES:
        ss.tf = st.query_params["tf"]

ICONS = dict(info=":material/info:", ok=":material/check_circle:", warn=":material/warning:", error=":material/error:")


def notify(msg: str, kind: str = "info") -> None:
    """Queue a toast. Queued, not shown at once, so a note made just before st.rerun() survives it."""
    ss.notes.append((msg, kind))


def flush_notes() -> None:
    for msg, kind in ss.notes:
        st.toast(msg, icon=ICONS[kind], duration="long" if kind in ("warn", "error") else "short")
    ss.notes = []


theme.inject_css("light" if ss.appearance == "Paper" else "dark")


# ── data ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_bars(ticker: str, tfk: str):
    df, meta = D.fetch(ticker, D.TIMEFRAMES[tfk])
    keep = {k: meta.get(k) for k in ("priceHint", "exchangeName", "fullExchangeName", "longName", "shortName", "currency",
                                     "exchangeTimezoneName", "instrumentType", "builtFrom", "patched", "regularMarketTime",
                                     "currentTradingPeriod")}
    keep["fetchedAt"] = pd.Timestamp.now(tz="UTC")
    return df.iloc[-P.CALC_BARS:], keep


@st.cache_data(ttl=900, show_spinner=False)
def load_avail(ticker: str) -> dict:
    return D.availability(ticker)


@st.cache_data(ttl=300, show_spinner=False)
def load_intrabars(ticker: str, tfk: str, naked_age: int, n_bars: int, last_ts: int):
    df, _ = load_bars(ticker, tfk)
    return D.fetch_intrabars(ticker, D.TIMEFRAMES[tfk], df, naked_age)


@st.cache_data(ttl=120, show_spinner=False)
def load_quotes(tickers: tuple[str, ...]):
    """{ticker: (last, change, change %)} off the same repaired daily bars the chart draws (D.quote)."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(8) as ex:
        got = list(ex.map(D.quote, tickers))
    return {tk: q for tk, q in zip(tickers, got) if q}


# ── settings: every input of the script, as the script words it ────────────
@st.dialog("Anumaan · Settings", width="large")
def settings_dialog():
    specs = I.load()
    cur = ss.inputs
    groups = list(dict.fromkeys(s["group"] for s in specs))
    new = dict(cur)
    for g, tab in zip(groups, st.tabs([g.split(" · ", 1)[-1] for g in groups])):
        with tab:
            for s in [x for x in specs if x["group"] == g]:
                f, lab, tip = s["field"], (" " * (s["indent"] // 4)) + s["label"], s["tooltip"]
                key = f"set_{f}"
                if s["kind"] == "bool":
                    new[f] = st.checkbox(lab, value=bool(cur[f]), help=tip, key=key)
                elif s["kind"] == "string":
                    opts = s["options"] or [cur[f]]
                    new[f] = st.selectbox(lab, opts, index=opts.index(cur[f]) if cur[f] in opts else 0, help=tip, key=key)
                elif s["kind"] == "int":
                    new[f] = int(st.number_input(lab, value=int(cur[f]), min_value=int(s["minval"]) if s["minval"] is not None else None,
                                                 max_value=int(s["maxval"]) if s["maxval"] is not None else None,
                                                 step=int(s["step"] or 1), help=tip, key=key))
                else:
                    stp = s["step"] or 0.01
                    dec = max(0, -int(math.floor(math.log10(stp)))) if stp < 1 else 0
                    new[f] = float(st.number_input(lab, value=float(cur[f]), min_value=s["minval"], max_value=s["maxval"], step=stp,
                                                   format=f"%.{max(dec, 1)}f", help=tip, key=key))
    c1, c2, c3 = st.columns([1, 1, 1])
    if c1.button("Defaults", width="stretch"):
        ss.inputs = P.Inputs().as_dict()
        for k in list(ss.keys()):
            if str(k).startswith("set_"):
                del ss[k]
        notify("Settings restored to the script's defaults.", "ok")
        st.rerun()
    if c2.button("Cancel", width="stretch"):
        st.rerun()
    if c3.button("Ok", type="primary", width="stretch"):
        changed = sum(new[k] != cur[k] for k in new)
        ss.inputs = new
        notify(f"Settings applied · {changed} changed." if changed else "No settings changed.", "ok" if changed else "info")
        st.rerun()


flush_notes()


def refresh_data() -> None:
    for f in (load_bars, load_avail, load_quotes, load_intrabars):
        f.clear()
    ss.refreshed = True          # told at the end of the run, once the new data is in, not as the reload starts


# ── symbol and what Yahoo has for it, before the toolbar draws ──────────────
# The interval control dims the intervals Yahoo has no bars for, so the symbol is checked first. A symbol with no
# data at all goes back to the last one that loaded, with a note saying why.
name, ticker, exchange, description = D.resolve(ss.symbol)
with st.spinner(f"Looking up {name}…"):
    try:
        avail = load_avail(ticker)
    except Exception:
        avail = {k: "" for k in INTERVALS}          # cannot tell: let the bars request decide
if all(avail.values()):
    if ss.last_good and D.resolve(ss.last_good)[1] != ticker:
        known = ss.symbol.strip().upper().split(":")[-1] in D.UNAVAILABLE
        notify(f"{ss.symbol}: {D.hint(ss.symbol)}" if known else f"No data for {ss.symbol} on Yahoo. {D.hint(ss.symbol)}", "error")
        ss.symbol = ss.last_good
        st.rerun()
if avail.get(ss.tf) and not avail.get("D"):
    notify(f"{ss.tf} is not available for {name}: {avail[ss.tf]}. Showing D.", "warn")
    ss.tf = "D"
ss.avail = avail
# Widget state follows the app's state, set before the widgets draw: a click on the selected segment no longer
# leaves the control with nothing selected, and a fallback to D shows on the control at once.
ss.tf_seg, ss.pane_seg, ss.ap_seg = ss.tf, ss.inputs["pane"], ss.appearance

top = st.empty()                      # the command bar, filled once the data is in: identity comes first on the page

# ── toolbar ────────────────────────────────────────────────────────────────
def _set_symbol():
    v = (ss.get("sym_in") or "").strip()
    if v:
        ss.symbol = v
        ss.sym_in = ""


def _set_tf():
    v = ss.tf_seg
    if not v or v == ss.tf:
        return
    why = (ss.get("avail") or {}).get(v)
    if why:
        notify(f"{v} is not available: {why}.", "warn")
    else:
        ss.tf = v


def _set_pane():
    if ss.pane_seg:
        ss.inputs = {**ss.inputs, "pane": ss.pane_seg}


def _set_appearance():
    if ss.ap_seg:
        ss.appearance = ss.ap_seg


with st.container(key="toolbar"):
    # Three groups, left to right: what you are looking at (symbol, interval), how it is drawn (pane, volume), and the
    # app's own controls (refresh, the script's inputs, appearance) - pushed right by an empty spacer column.
    tcols = st.columns([1, 1, 1, 1, 1, 1, 1], gap="small", vertical_alignment="center")
    with tcols[0]:
        st.text_input("Symbol", key="sym_in", placeholder=f"{ss.symbol}", label_visibility="collapsed", on_change=_set_symbol,
                      help="Type a symbol and press Enter: NIFTY, NSE:TCS, AAPL, GC=F, BTC-USD, or any Yahoo ticker. Press / anywhere to jump here.")
    with tcols[1]:
        st.segmented_control("Interval", INTERVALS, key="tf_seg", label_visibility="collapsed", on_change=_set_tf)
        off = [i + 1 for i, k in enumerate(INTERVALS) if avail.get(k)]
        if off:   # the intervals Yahoo has no bars for: dimmed, and a click says why instead of loading nothing
            st.html("<style>" + ",".join(f".st-key-tf_seg button:nth-of-type({i})" for i in off) +
                    "{opacity:.38;text-decoration:line-through;text-decoration-thickness:1px}</style>")
    with tcols[2]:
        st.segmented_control("Pane", ["Surprise", "Proof"], key="pane_seg", label_visibility="collapsed", on_change=_set_pane)
    with tcols[3]:
        vol = st.segmented_control("Volume", ["Volume"], selection_mode="multi", default=["Volume"] if ss.volume else [],
                                   key="vol_seg", label_visibility="collapsed")
        ss.volume = "Volume" in (vol or [])
    with tcols[5]:
        with st.container(horizontal=True, gap="small", key="tb_actions"):
            st.button("", icon=":material/refresh:", key="tb_refresh", on_click=refresh_data,
                      help="Reload bars and quotes from Yahoo. They are kept for 5 minutes (quotes 2) between loads.")
            if st.button("Settings", icon=":material/tune:", key="tb_settings", help="Every input of the script, as the script words it."):
                settings_dialog()
    with tcols[6]:
        st.segmented_control("Appearance", ["Slate", "Paper"], key="ap_seg", label_visibility="collapsed", on_change=_set_appearance)

# ── compute ────────────────────────────────────────────────────────────────
tfo = D.TIMEFRAMES[ss.tf]
inp = P.Inputs(**ss.inputs)
dark_app = ss.appearance == "Slate"
dark = inp.theme == "Dark" or (inp.theme == "Auto" and dark_app)

with st.spinner(f"Loading {name} · {ss.tf}…"):
    try:
        df, meta = load_bars(ticker, ss.tf)
        err = ""
    except Exception as exc:  # network, or Yahoo refusing the request
        df, meta, err = pd.DataFrame(), {}, f"{type(exc).__name__}: {exc}"

if df is None or len(df) < 30:
    n_got = 0 if df is None else len(df)
    if ss.tf != "D" and not err:
        # Too few bars on this interval (a short intraday history): fall back to the daily chart, and say so.
        notify(f"{name} has {n_got} bars on {ss.tf} at Yahoo; the script needs 30. Showing D.", "warn")
        ss.tf = "D"
        st.rerun()
    if ss.last_good and D.resolve(ss.last_good)[1] != ticker and not err:
        notify(f"{name} has {n_got} daily bars at Yahoo; the script needs 30. Back to {ss.last_good}.", "error")
        ss.symbol = ss.last_good
        st.rerun()
    with top.container():
        K.command_bar(name=name, description=description or "—", price=None, change_pct=None, decimals=2, meta=[("Interval", ss.tf)],
                      status=("No data", "danger"))
    with st.container(key="nodata"):
        st.markdown(f'<div class="notice notice-error"><b>No chart for {name} on {ss.tf}.</b> '
                    + (f"Yahoo could not be reached or refused the request ({err[:160]}). " if err else
                       (f"Yahoo has no data for {ss.symbol}. " if n_got == 0 else f"Yahoo returned {n_got} bars; the script needs 30. ")
                       + f"{D.hint(ss.symbol)} ")
                    + "Yahoo serves 1m for 7 days, 5m-30m for 60 days and 1h for 730 days.</div>", unsafe_allow_html=True)
        st.button("Try again", icon=":material/refresh:", on_click=refresh_data, key="retry")
    flush_notes()
    st.stop()

ss.last_good = ss.symbol
if st.query_params.get("symbol") != ss.symbol or st.query_params.get("tf") != ss.tf:
    st.query_params.update(symbol=ss.symbol, tf=ss.tf)
if ticker not in ss.recent:
    ss.recent = ([ticker] + ss.recent)[:8]
mintick = D.mintick_of(meta, df)
decimals = max(0, int(round(-math.log10(mintick)))) if mintick > 0 else 2
pal = palette(dark)


def engine_failed(stage: str, exc: Exception) -> None:
    """The script could not run on these bars: say so and step back (to D, else to the last symbol that ran) instead of
    leaving a traceback where the chart should be."""
    msg = f"Anumaan could not {stage} on {name} · {ss.tf}: {type(exc).__name__}: {str(exc)[:140]}"
    if ss.tf != "D":
        notify(msg + ". Showing D.", "error")
        ss.tf = "D"
        st.rerun()
    if ss.get("last_ran") and ss.last_ran != ss.symbol:
        notify(msg + f". Back to {ss.last_ran}.", "error")
        ss.symbol = ss.last_ran
        st.rerun()
    with top.container():
        K.command_bar(name=name, description=description or "—", price=None, change_pct=None, decimals=2, meta=[("Interval", ss.tf)],
                      status=("Error", "danger"))
    st.markdown(f'<div class="notice notice-error"><b>{H.escape(msg)}.</b></div>', unsafe_allow_html=True)
    flush_notes()
    st.stop()


try:
    e = P.run(df, inp)
except Exception as exc:
    engine_failed("calculate", exc)
ib, ib_info = ({}, dict(pine_ltf=None, yf_ltf=None, bars_with_intrabars=0, volume_refilled=0))
ib_failed = False
no_intraday = all(avail.get(k) for k in ("1m", "5m", "1h"))     # a fund: daily bars only
if inp.vp and inp.vp_intrabar and not no_intraday:
    try:
        ib, ib_info = load_intrabars(ticker, ss.tf, inp.vp_naked_age, len(df), int(df.index[-1].value))
    except Exception:
        ib_failed = True
try:
    vp = PR.build(df, inp, tfo.sec, mintick, pal, ib, cone_on=inp.cone)
    vp["state"]["decimals"] = decimals
    TONES = dict(CONE=pal["CONE"], DN=pal["DN"], UP=pal["UP"], GOLD=pal["GOLD"], NEUT=pal["NEUT"], TEXT=pal["TEXT"])
    rows = TB.rows(e, float(df.close.iloc[-1]), decimals)
    for r in rows:
        r["color"] = TONES[r["tone"]]
except Exception as exc:
    engine_failed("draw its profile and table", exc)
ss.last_ran = ss.symbol

# ── command bar ────────────────────────────────────────────────────────────
last, prev = float(df.close.iloc[-1]), float(df.close.iloc[-2])
intraday = tfo.sec < 86400
if intraday:
    # The header's change is against the previous session's close on every interval, not against the bar before.
    qd = load_quotes((ticker,)).get(ticker)
    if qd and qd[0] - qd[1] > 0:
        prev = qd[0] - qd[1]
ex_name = meta.get("fullExchangeName") or meta.get("exchangeName") or exchange
tz = meta.get("exchangeTimezoneName") or "UTC"
now = pd.Timestamp.now(tz=tz)
# Market state from Yahoo's current trading period: open while now is inside its regular session.
reg = (meta.get("currentTradingPeriod") or {}).get("regular") or {}
try:
    is_open = pd.Timestamp(reg["start"]) <= now <= pd.Timestamp(reg["end"])
except Exception:
    is_open = None
try:
    as_of = pd.Timestamp(meta["regularMarketTime"]).tz_convert(tz)
except Exception:
    as_of = None
as_of_txt = "" if as_of is None else as_of.strftime("%d %b %H:%M %Z") if as_of.date() != now.date() else as_of.strftime("%H:%M %Z")
market = (("Market open", "success") if is_open else ("Market closed", "neutral")) if is_open is not None else None
profile_txt = (f"{ib_info.get('yf_ltf')} intrabars" if ib_info.get("bars_with_intrabars") else "bar ranges") if inp.vp else ""
with top.container():
  K.command_bar(
    name=name, description=meta.get("longName") or meta.get("shortName") or description, price=last, change_pct=(last / prev - 1) * 100,
    decimals=decimals,
    meta=[("Exchange", ex_name or "—"), ("Interval", ss.tf), ("Bars", f"{len(df):,} of {P.CALC_BARS:,}"),
          ("Last bar", df.index[-1].strftime("%d %b %Y %H:%M" if intraday else "%d %b %Y")), ("As of", as_of_txt),
          ("Currency", meta.get("currency") or ""), ("Profile", profile_txt)],
    status=market,
)

# ── notices: what the viewer should know about this chart's data, while it holds ──
# Events (a fallback, a refresh, a bad symbol) are toasts; these are conditions of the chart in front of you.
notices = []
pt = meta.get("patched")
if pt and not intraday:
    days = ", ".join(f"{pd.Timestamp(d):%d %b}" for d in pt["sessions"])
    notices.append(("info", f"Yahoo's daily bars for {ticker} stop at {pd.Timestamp(pt['after']):%d %b}. The {days} session is built "
                            "from its hourly bars and closes at the exchange's official close"
                            + ("; Yahoo has no volume for it yet." if not (df["volume"].iloc[-len(pt["sessions"]):] > 0).any()
                               and (df["volume"] > 0).any() else ".")))
if meta.get("builtFrom") and not intraday:
    notices.append(("info", f"Yahoo keeps a single daily bar for {ticker}: its {ss.tf} bars are built from its hourly bars, which "
                            f"start {df.index[0]:%d %b %Y}."))
sig_last = e["series"]["sig"][-1]
if sig_last != sig_last:
    need = 252 + int(inp.H)
    better = [k for k in ("D", "1h", "4h") if k != ss.tf and not avail.get(k)]
    notices.append(("warn", f"Anumaan is warming up: its risk forecast needs {need} bars and this {ss.tf} chart has {len(df)}, so the "
                            "cone, stops and exposure are not drawn yet." + (f" {better[0]} has enough." if better and ss.tf in ("W", "M") else "")))
# A feed that has fallen behind: while the market is open, the last bar should be recent.
if is_open:
    lag = now - df.index[-1].tz_convert(tz) if df.index.tz is not None else pd.Timedelta(0)
    allowed = pd.Timedelta(seconds=3 * tfo.sec) + pd.Timedelta(minutes=30) if intraday else pd.Timedelta(days=1)
    if (intraday and lag > allowed) or (not intraday and df.index[-1].tz_convert(tz).date() < now.date() and ss.tf == "D"):
        notices.append(("warn", f"The market is open but Yahoo's last {ss.tf} bar is from "
                                f"{df.index[-1].tz_convert(tz):%d %b %H:%M %Z}: the feed is behind. Refresh in a few minutes."))
if ss.volume and not (df["volume"].fillna(0) > 0).any():
    notices.append(("info", f"Yahoo reports no volume for {ticker}, so the volume histogram is empty."))
if inp.vp and inp.vp_intrabar and no_intraday:
    notices.append(("info", f"Yahoo has no intraday bars for {ticker}: the profile spreads each bar's volume evenly over its range, "
                            "as the script does where intrabars do not reach."))
if ib_failed:
    notices.append(("warn", "Intrabars could not be loaded from Yahoo: the profile spreads each bar's volume evenly over its range."))
if notices:
    with st.container(key="notices"):
        K.notices(notices)

# ── chart and rail ─────────────────────────────────────────────────────────
workspace = st.container(key="workspace")
left, rail = workspace.columns([4.3, 1.25], gap="small")
tok = C.tokens(dark_app)
with left:
    with st.container(key="chartframe"):
        payload = C.payload(df, e, vp, meta, pal, dark, tok, tfo.sec, decimals, mintick, show_volume=ss.volume, table_rows=rows)
        title = dict(name=name, tf=ss.tf, exchange=ex_name or "", watermark=f"{name}, {ss.tf}")
        components.html(C.html(payload, tok, title, height=CHART_H), height=CHART_H, scrolling=False)

with rail:
    tickers = tuple(dict.fromkeys([w[1] for w in D.WATCHLIST] + ss.recent))
    q = load_quotes(tickers)
    unquoted = sum(tk not in q for tk in tickers)
    with K.panel("watch", "Watchlist", meta="1D change · click to open" + (f" · {unquoted} unquoted" if 0 < unquoted < len(tickers) else "")):
        info = {w[1]: w for w in D.WATCHLIST}
        wrows = []
        for tk in tickers:
            lastq, chg, pct = q.get(tk, (None, None, None))      # no quote: the row stays, with dashes, so the list keeps its shape
            w = info.get(tk, (tk, tk, "", tk, "Recent", 2 if (lastq or 0) >= 10 else 4))
            wrows.append(dict(sym=w[0], desc=w[3], last=lastq, chg=chg, pct=pct, dec=w[5], section=w[4], active=(tk == ticker)))
        if q:
            wt = (dict(ink="#E6EAF1", tertiary="#8B95A6", quaternary="#737D8E", line="rgba(255,255,255,0.13)", lineFaint="rgba(255,255,255,0.05)",
                       up="#089981", down="#F23645", accent="#4C7DF0", active="rgba(76,125,240,0.10)", hover="#151920", bg="#0F1217") if dark_app else
                  dict(ink="#141920", tertiary="#5E6979", quaternary="#6B7482", line="rgba(15,23,42,0.18)", lineFaint="rgba(15,23,42,0.06)",
                       up="#089981", down="#F23645", accent="#2B5FD9", active="rgba(43,95,217,0.07)", hover="#EEF1F5", bg="#FFFFFF"))
            clicked = K.watchlist(wrows, wt, cap=WATCH_H, key="watchlist")
            if clicked and clicked.get("nonce") != ss.get("watch_nonce"):
                ss.watch_nonce = clicked.get("nonce")
                if clicked.get("symbol") and clicked["symbol"] != name:
                    ss.symbol = clicked["symbol"]
                    st.rerun()
        else:
            K.note("Quotes unavailable right now.")
    with K.panel("details", "Symbol", context=ticker):
        hi52 = df.high.iloc[-252:].max() if not intraday else df.high.max()
        lo52 = df.low.iloc[-252:].min() if not intraday else df.low.min()
        kind = (meta.get("instrumentType") or "").replace("_", " ").title()
        K.kv_list([("Exchange", " · ".join(x for x in (ex_name, kind) if x) or "—"),
                   ("Day range", f"{df.low.iloc[-1]:,.{decimals}f} – {df.high.iloc[-1]:,.{decimals}f}"),
                   ("52-week range" if not intraday else "Loaded range", f"{lo52:,.{decimals}f} – {hi52:,.{decimals}f}"),
                   # What the command bar has no room for on a tablet (kv-x) or a phone (kv-x and kv-p); hidden on a desktop,
                   # where the command bar shows it and the box keeps its three rows.
                   ("Bars", f"{len(df):,} of {P.CALC_BARS:,}", "kv-x"),
                   ("Currency", meta.get("currency") or "—", "kv-x"),
                   ("Profile", profile_txt or "off", "kv-x"),
                   ("Last bar", df.index[-1].strftime("%d %b %Y %H:%M" if intraday else "%d %b %Y"), "kv-p"),
                   ("As of", as_of_txt or "—", "kv-p")])

# ── bottom panel ───────────────────────────────────────────────────────────
# Three questions, in the order a trader asks them, and the record of what changed.
tabs = st.tabs(["Plan", "Forecast", "Audit", "Events"])
# Each tab draws on its own: one that fails says so in its place, and the others still draw.
for tab, draw in zip(tabs, (lambda: PN.plan(e, vp, df, decimals, meta.get("currency") or "", intraday, tok),
                            lambda: PN.forecast(e, df, tok, decimals), lambda: PN.audit(e, df, tok),
                            lambda: PN.events(e, df, intraday, decimals))):
    with tab:
        try:
            draw()
        except Exception as exc:
            st.markdown(f'<div class="notice notice-error"><b>This tab could not be drawn for {H.escape(name)} · {ss.tf}.</b>'
                        f'&nbsp;{H.escape(type(exc).__name__)}: {H.escape(str(exc)[:200])}</div>', unsafe_allow_html=True)

refill = (f" · Yahoo has no intraday volume for {ticker}: on {ib_info['volume_refilled']} bars the profile shares each bar's own "
          "volume over its intrabars") if ib_info.get("volume_refilled") else ""
st.markdown(
    '<div class="t-foot">Anumaan · anumaan.pine ported to Python bar for bar · data: Yahoo Finance (delayed)' + refill + ' · charts by '
    '<a href="https://www.tradingview.com/" target="_blank" rel="noopener">TradingView Lightweight Charts™</a>, Apache-2.0</div>',
    unsafe_allow_html=True)
if ss.pop("refreshed", False):
    notify(f"Data refreshed from Yahoo · {pd.Timestamp.now(tz=tz):%H:%M:%S %Z}.", "ok")
flush_notes()
