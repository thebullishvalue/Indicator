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

theme.inject_css("light" if ss.appearance == "Paper" else "dark")


# ── data ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_bars(ticker: str, tfk: str):
    df, meta = D.fetch(ticker, D.TIMEFRAMES[tfk])
    return df.iloc[-P.CALC_BARS:], {k: meta.get(k) for k in ("priceHint", "exchangeName", "fullExchangeName", "longName",
                                                                 "shortName", "currency", "exchangeTimezoneName", "instrumentType")}


@st.cache_data(ttl=300, show_spinner=False)
def load_intrabars(ticker: str, tfk: str, naked_age: int, n_bars: int, last_ts: int):
    df, _ = load_bars(ticker, tfk)
    return D.fetch_intrabars(ticker, D.TIMEFRAMES[tfk], df, naked_age)


@st.cache_data(ttl=120, show_spinner=False)
def load_quotes(tickers: tuple[str, ...]):
    import yfinance as yf
    out = {}
    try:
        raw = yf.download(list(tickers), period="7d", interval="1d", group_by="ticker", progress=False, threads=True, auto_adjust=False)
    except Exception:
        return out
    for tk in tickers:
        try:
            c = raw[tk]["Close"].dropna()
            if len(c) >= 2:
                out[tk] = (float(c.iloc[-1]), float(c.iloc[-1] - c.iloc[-2]), float(c.iloc[-1] / c.iloc[-2] - 1) * 100)
        except Exception:
            pass
    return out


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
        st.rerun()
    if c2.button("Cancel", width="stretch"):
        st.rerun()
    if c3.button("Ok", type="primary", width="stretch"):
        ss.inputs = new
        st.rerun()


top = st.empty()                      # the command bar, filled once the data is in: identity comes first on the page

# ── toolbar ────────────────────────────────────────────────────────────────
def _set_symbol():
    v = (ss.get("sym_in") or "").strip()
    if v:
        ss.symbol = v
        ss.sym_in = ""


with st.container(key="toolbar"):
    # Three groups, left to right: what you are looking at (symbol, interval), how it is drawn (pane, volume), and the
    # app's own settings (the script's inputs, appearance) - pushed right by an empty spacer column.
    tcols = st.columns([1, 1, 1, 1, 1, 1, 1], gap="small", vertical_alignment="center")
    with tcols[0]:
        st.text_input("Symbol", key="sym_in", placeholder=f"{ss.symbol}", label_visibility="collapsed", on_change=_set_symbol,
                      help="Type a symbol and press Enter: NIFTY, NSE:TCS, AAPL, GC=F, BTC-USD, or any Yahoo ticker.")
    with tcols[1]:
        tf = st.segmented_control("Interval", INTERVALS, default=ss.tf, key="tf_seg", label_visibility="collapsed")
        if tf and tf != ss.tf:
            ss.tf = tf
    with tcols[2]:
        pane = st.segmented_control("Pane", ["Surprise", "Proof"], default=ss.inputs["pane"], key="pane_seg", label_visibility="collapsed")
        if pane and pane != ss.inputs["pane"]:
            ss.inputs = {**ss.inputs, "pane": pane}
    with tcols[3]:
        vol = st.segmented_control("Volume", ["Volume"], selection_mode="multi", default=["Volume"] if ss.volume else [],
                                   key="vol_seg", label_visibility="collapsed")
        ss.volume = "Volume" in (vol or [])
    with tcols[5]:
        if st.button("Settings", icon=":material/tune:", help="Every input of the script, as the script words it."):
            settings_dialog()
    with tcols[6]:
        ap = st.segmented_control("Appearance", ["Slate", "Paper"], default=ss.appearance, key="ap_seg", label_visibility="collapsed")
        if ap and ap != ss.appearance:
            ss.appearance = ap
            st.rerun()

# ── compute ────────────────────────────────────────────────────────────────
name, ticker, exchange, description = D.resolve(ss.symbol)
tfo = D.TIMEFRAMES[ss.tf]
inp = P.Inputs(**ss.inputs)
dark_app = ss.appearance == "Slate"
dark = inp.theme == "Dark" or (inp.theme == "Auto" and dark_app)

with st.spinner(f"Loading {name} · {ss.tf}…"):
    try:
        df, meta = load_bars(ticker, ss.tf)
    except Exception as exc:  # network or unknown symbol
        df, meta = pd.DataFrame(), {}
        err = str(exc)
    else:
        err = ""

if df is None or len(df) < 30:
    with top.container():
            K.command_bar(name=name, description=description or "—", price=None, change_pct=None, decimals=2, meta=[("Interval", ss.tf)],
                      status=("No data", "danger"))
    st.error(f"No bars for **{ticker}** on **{ss.tf}**. {err} Yahoo serves 1m for 7 days, 5m-30m for 60 days and 1h for 730 days.")
    st.stop()

if ticker not in ss.recent:
    ss.recent = ([ticker] + ss.recent)[:8]
mintick = D.mintick_of(meta, df)
decimals = max(0, int(round(-math.log10(mintick)))) if mintick > 0 else 2
pal = palette(dark)
e = P.run(df, inp)
ib, ib_info = ({}, dict(pine_ltf=None, yf_ltf=None, bars_with_intrabars=0, volume_refilled=0))
if inp.vp and inp.vp_intrabar:
    try:
        ib, ib_info = load_intrabars(ticker, ss.tf, inp.vp_naked_age, len(df), int(df.index[-1].value))
    except Exception:
        pass
vp = PR.build(df, inp, tfo.sec, mintick, pal, ib, cone_on=inp.cone)
vp["state"]["decimals"] = decimals
TONES = dict(CONE=pal["CONE"], DN=pal["DN"], UP=pal["UP"], GOLD=pal["GOLD"], NEUT=pal["NEUT"], TEXT=pal["TEXT"])
rows = TB.rows(e, float(df.close.iloc[-1]), decimals)
for r in rows:
    r["color"] = TONES[r["tone"]]

# ── command bar ────────────────────────────────────────────────────────────
last, prev = float(df.close.iloc[-1]), float(df.close.iloc[-2])
intraday = tfo.sec < 86400
ex_name = meta.get("fullExchangeName") or meta.get("exchangeName") or exchange
ib_note = (f"Intrabars {ib_info.get('yf_ltf')} · {ib_info.get('bars_with_intrabars', 0)} bars" if ib_info.get("bars_with_intrabars")
           else "Profile · bar ranges")
with top.container():
  K.command_bar(
    name=name, description=meta.get("longName") or meta.get("shortName") or description, price=last, change_pct=(last / prev - 1) * 100,
    decimals=decimals,
    meta=[("Exchange", ex_name or "—"), ("Interval", ss.tf), ("Bars", f"{len(df):,} of {P.CALC_BARS:,}"),
          ("Last bar", df.index[-1].strftime("%d %b %Y %H:%M" if intraday else "%d %b %Y")), ("Currency", meta.get("currency") or "")],
    status=(ib_note, "info" if ib_info.get("bars_with_intrabars") else "neutral"),
)

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
    with K.panel("watch", "Watchlist", meta="1D change · click to open"):
        tickers = tuple(dict.fromkeys([w[1] for w in D.WATCHLIST] + ss.recent))
        q = load_quotes(tickers)
        info = {w[1]: w for w in D.WATCHLIST}
        wrows = []
        for tk in tickers:
            if tk not in q:
                continue
            w = info.get(tk, (tk, tk, "", tk))
            lastq, chg, pct = q[tk]
            dq = 2 if lastq >= 10 else 4
            wrows.append(dict(sym=w[0], desc=w[3], last=lastq, chg=chg, pct=pct, dec=dq, active=(tk == ticker)))
        if wrows:
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
                   ("52-week range" if not intraday else "Loaded range", f"{lo52:,.{decimals}f} – {hi52:,.{decimals}f}")])

# ── bottom panel ───────────────────────────────────────────────────────────
# Three questions, in the order a trader asks them, and the record of what changed.
tabs = st.tabs(["Plan", "Forecast", "Audit", "Events"])
with tabs[0]:
    PN.plan(e, vp, df, decimals, meta.get("currency") or "", intraday, tok)
with tabs[1]:
    PN.forecast(e, df, tok, decimals)
with tabs[2]:
    PN.audit(e, df, tok)
with tabs[3]:
    PN.events(e, df, intraday, decimals)

refill = (f" · Yahoo has no intraday volume for {ticker}: on {ib_info['volume_refilled']} bars the profile shares each bar's own "
          "volume over its intrabars") if ib_info.get("volume_refilled") else ""
st.markdown(
    '<div class="t-foot">Anumaan · anumaan.pine ported to Python bar for bar · data: Yahoo Finance (delayed)' + refill + ' · charts by '
    '<a href="https://www.tradingview.com/" target="_blank" rel="noopener">TradingView Lightweight Charts™</a>, Apache-2.0</div>',
    unsafe_allow_html=True)
