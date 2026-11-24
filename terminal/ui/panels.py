"""The bottom panel, arranged by the three questions a trader brings to this chart:

    Plan      what do I do now?          exposure, risk, trend, the cone, position size at the stops, every level
    Forecast  how far can it go?         the four horizons as a fan and a term structure, and what followed this state
    Audit     has it been honest here?   calibration by horizon, regime and trend, surprises in band widths,
                                         the exposure's proof, the ledger
    Events    what changed, and when?    every alert condition as it fired, filterable
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from engine.table import f_pct, fmt, st_name, words
from ui import components as K

ALERT_TEXT = {
    "Landing band · close above": "closed above the landing band. A miss, not a signal.",
    "Landing band · close below": "closed below the landing band. A miss, not a signal.",
    "Stretch ladder · 3+ rungs above": "3 or 4 ladder rungs closed above their bands. No measured direction.",
    "Stretch ladder · 3+ rungs below": "3 or 4 ladder rungs closed below their bands. Long stops are touched more often than stated here.",
    "Risk · stressed": "risk entered the top third of its last 500 bars. Cone and stops widen; exposure falls.",
    "Risk · rising": "risk rose more than 10% in one horizon. Such rises usually fade.",
    "Midline · close above": "closed above the midline. Not a signal.",
    "Midline · close below": "closed below the midline. Not a signal.",
    "Exposure · changed": "exposure moved one step. See the table's EXPOSURE row.",
    "Ledger · proven state, positive": "entered a state this chart's history has proven positive. This chart's own record only.",
    "Ledger · proven state, negative": "entered a state this chart's history has proven negative. This chart's own record only.",
}
CATEGORY = {"Landing band": "Misses", "Stretch ladder": "Ladder", "Risk": "Risk", "Midline": "Midline", "Exposure": "Exposure",
            "Ledger": "Ledger"}


# Every panel's height is arithmetic, so side-by-side panels can be made equal: a panel is 2px of border and a 42px header,
# a table is a 34px header row and 34px rows (terminal.css fixes both), a plotly chart is exactly its height (no padding),
# rows of panels are 12px apart. Prose lives behind each header's (i), not in the body.
PANEL, HDR, ROW, GAP, PLOT_PAD, INPUTS = 44, 34, 34, 12, 0, 89


def _table_h(rows: int) -> int:
    return HDR + rows * ROW


def _na(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


def _stamp(ts, intraday: bool) -> str:
    return ts.strftime("%Y-%m-%d %H:%M" if intraday else "%Y-%m-%d")


def _px(x, dec):
    return "—" if _na(x) else f"{x:,.{dec}f}"


def _sg(x, spec: str = ".2f") -> str:
    """A signed number as the family prints one: +1.23 or −0.64 (a typographic minus); zero carries no sign."""
    if _na(x):
        return "—"
    out = format(x, "+" + spec)
    return out[1:] if float(out.rstrip("%")) == 0 else out.replace("-", "−")


def _signed_pct(x, dec: int = 2) -> str:
    return "—" if _na(x) else _sg(100 * x, f".{dec}f") + "%"


def _fig(tok: dict, height: int) -> dict:
    # The hover is the family's: the panel's own surface, the data face, every series' name in full (Plotly cut
    # "Following exposure" to "Following ex..."), and the numbers formatted here in Python (see _bins).
    return dict(height=height, margin=dict(l=16, r=16, t=8, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono, monospace", size=10, color=tok["axis"]), hovermode="x unified",
                hoverlabel=dict(bgcolor=tok["bg"], bordercolor=tok["border"], align="left", namelength=-1,
                                font=dict(family="JetBrains Mono, monospace", size=11, color=tok["ink"])),
                # the legend's colour is named: Streamlit's Plotly template paints it from its own dark base, near-white
                # (250, 250, 250) on Paper, over the layout's font
                legend=dict(orientation="h", y=1.08, x=0, bgcolor="rgba(0,0,0,0)",
                            font=dict(family="JetBrains Mono, monospace", size=10, color=tok["axis"])))


def _edge(v: float) -> str:
    """A bin edge in σ or band widths: as few places as it needs, signed."""
    out = _sg(v, ".3f")
    return out.rstrip("0").rstrip(".") if "." in out else out


def _bins(v: np.ndarray, start: float, end: float, size: float):
    """A probability histogram drawn as bars, so its hover can say what a bin is ("−1 to −0.5σ") rather than Plotly's
    "−1 - −0.501": centres, shares of all the values, counts, and each bin's (lo, hi)."""
    edges = np.arange(start, end + size / 2, size)
    n, _ = np.histogram(v, bins=edges)
    share = n / len(v) if len(v) else n.astype(float)
    return (edges[:-1] + edges[1:]) / 2, share, n, list(zip(edges[:-1], edges[1:]))


def _date_fmt(intraday: bool) -> str:
    return "%d %b %Y %H:%M" if intraday else "%d %b %Y"


def _is_intraday(idx) -> bool:
    return len(idx) > 1 and (idx[-1] - idx[-2]).total_seconds() < 86400


def _chart(fig) -> None:
    # Every axis names its own colours. Streamlit's Plotly template paints tick labels, axis titles and the zero line
    # from its static dark base, over the layout's font: on Paper the labels were a faint near-white and the zero line
    # near-black. The axis tone is the page's (Paper #5E6979, Slate #8B95A6); the zero line is the panel's hairline.
    tone = _TOK.get("axis", "#8B95A6")
    for upd in (fig.update_xaxes, fig.update_yaxes):
        upd(tickfont=dict(color=tone), title_font=dict(color=tone), zerolinecolor=_TOK.get("border", "rgba(15,23,42,0.12)"),
            showline=False)           # gridlines only, as every member's charts
    st.plotly_chart(fig, width="stretch", config=dict(displayModeBar=False))


def _units(u: float) -> str:
    if _na(u):
        return "—"
    return f"{u:,.0f}" if u >= 100 else f"{u:,.2f}" if u >= 1 else f"{u:,.4f}"


# ═══ PLAN ═══════════════════════════════════════════════════════════════════
_TOK: dict = {}


def tok_axis() -> str:
    return _TOK.get("axis", "#8B95A6")


def plan(e: dict, vp: dict, df: pd.DataFrame, decimals: int, currency: str, intraday: bool, tok: dict) -> None:
    _TOK.clear(); _TOK.update(tok)
    s, L, inp = e["series"], e["last"], e["inputs"]
    t = e["n"] - 1
    W = words(e, t)
    c = float(df.close.iloc[-1])
    H = inp.H
    sig, sH = s["sig"][t], s["sH"][t]
    if _na(sig):
        K.note(f"The risk forecast needs a year of bars before its first reading ({t + 1} of {252 + H}).")
        return
    lo, hi, stopL, stopS = s["lower"][t], s["upper"][t], s["stopL"][t], s["stopS"][t]
    nF = L["nF"]
    K.kpi_strip([
        dict(label="Exposure", value=f_pct(s["E"][t], "#"),
             subtext=f"risk {f_pct(s['dialR'][t], '#')} × trend {f_pct(s['dialT'][t], '#')} · steps of {f_pct(inp.step, '#')}",
             tooltip="The share of a full position to carry: the instrument's usual risk over its risk now, cut in a downtrend, changed only in steps."),
        dict(label=f"Risk · {H} bars", value=f"±{f_pct(sH, '#.0')}", tone="warning" if s["regRaw"][t] == 2 else "neutral",
             subtext=f"{W['regTxt']} · rank {fmt(s['prk'][t], '#')} of 100 · {W['rmWord']}",
             tooltip="One standard move over the horizon; where risk stands among its last 500 bars; whether it rose or fell over the horizon."),
        dict(label="Trend", value=W["trTxt"], tone="success" if s["trRaw"][t] == 2 else "danger" if s["trRaw"][t] == 0 else "neutral",
             subtext=f"ladder {W['ladShort']}",
             tooltip="The move over a quarter, a half and a year of bars, in units of today's risk. The ladder: the four horizons' surprises against their bands."),
        dict(label=f"Cone {fmt(inp.cover, '#')}% · {H} bars", value=f"{_px(lo, decimals)} – {_px(hi, decimals)}",
             subtext=f"{f_pct(math.log(hi / lo), '#.0')} wide · {_signed_pct(lo / c - 1, 1)} / {_signed_pct(hi / c - 1, 1)}"),
        dict(label="Held here", value=f_pct(L["cov"], "#.0"),
             tone="warning" if (not _na(L["cov"]) and abs(L["cov"] - inp.cover / 100) > 0.03) else "neutral",
             subtext=f"of {nF:,} forecasts · stops {f_pct(L['nMS'] / nF if nF else float('nan'), '#')} / {f_pct(L['nMR'] / nF if nF else float('nan'), '#')}",
             tooltip=f"How often this chart's cone held (target {fmt(inp.cover, '#')}%) and its long / short stops were touched (target {fmt(inp.stop, '#')}%)."),
    ], key="kpi-plan", max_cols=5)

    st_ = vp["state"]
    lv = [("Short stop", stopS), ("Cone · upper", hi), ("Cone · lower", lo), ("Long stop", stopL),
          ("Landing band · upper", s["upper"][t - H] if t >= H else float("nan")),
          ("Landing band · lower", s["lower"][t - H] if t >= H else float("nan")), ("Midline", s["midL"][t]),
          ("POC", st_["poc"]), ("VAH", st_["vah"]), ("VAL", st_["val"]), ("VWAP", st_["vwap"]),
          ("Prior POC", st_["prev_poc"]), ("Prior VAH", st_["prev_vah"]), ("Prior VAL", st_["prev_val"])]
    if intraday:
        lv += [("IBH", st_["ibh"]), ("IBL", st_["ibl"])]
    lv += [("Naked POC", y) for y, _ in st_.get("naked", []) if not _na(y) and y != st_["prev_poc"]]
    lv = [(k, v) for k, v in lv if not _na(v)]
    lv.append(("Close", c))
    lv.sort(key=lambda kv: -kv[1])

    # the two columns meet: the ladder sets the height, the risk chart takes what the sizing table leaves
    ladder_tbl = _table_h(len(lv))
    size_h = PANEL + INPUTS + _table_h(3)
    chart_h = max(220, PANEL + ladder_tbl - size_h - GAP - PANEL - PLOT_PAD)
    ladder_tbl = max(ladder_tbl, size_h + GAP + PANEL + chart_h + PLOT_PAD - PANEL)

    left, right = st.columns(2, gap="small")
    with left:
        with K.panel("size", "Position size", context="sized to lose a set share of equity at the script's stops",
                     help=f"Each stop is touched within {H} bars {fmt(inp.stop, '#')}% of the time. Above 100% of equity a size needs "
                          "leverage. The exposure row is the position the dial says to hold, before any stop."):
            with st.container(key="sizeinputs"):
                a_, b_ = st.columns(2, gap="small")
                equity = a_.number_input(f"Equity · {currency}" if currency else "Equity", min_value=0.0, value=1_000_000.0,
                                         step=10_000.0, format="%.0f", key="equity")
                risk = b_.number_input("Risk per trade · %", min_value=0.05, max_value=10.0, value=float(inp.risk), step=0.05,
                                       format="%.2f", key="risk_pct")
            rows = []
            for side, stop in (("Long", stopL), ("Short", stopS)):
                dist = abs(c - stop)
                units = equity * risk / 100.0 / dist if dist > 0 else float("nan")
                value = units * c
                rows.append({"Side": side, "Entry": _px(c, decimals), "Stop": _px(stop, decimals), "Distance": f_pct(dist / c, "#.00"),
                             "Units": _units(units), "Value": f"{value:,.0f}",
                             "Of equity": f_pct(value / equity if equity else float("nan"), "#"), "Loss at stop": f"{equity * risk / 100.0:,.0f}"})
            E = s["E"][t]
            ev = (E if not _na(E) else 0.0) * equity
            rows.append({"Side": "Exposure", "Entry": _px(c, decimals), "Stop": "—", "Distance": "—", "Units": _units(ev / c),
                         "Value": f"{ev:,.0f}", "Of equity": f_pct(E, "#"), "Loss at stop": "—"})
            K.table(pd.DataFrame(rows), align_left=("Side",))
        n = min(250, t + 1)
        with K.panel("riskexp", "Risk and exposure", context=f"the last {n} bars · risk's rank in its last 500, and the exposure it set",
                     help="Exposure is the instrument's usual risk over its risk now, cut in a downtrend: it falls as risk climbs its range. "
                          "The dotted lines split risk into calm, normal and stressed thirds."):
            idx = df.index[-n:]
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.55, 0.45], vertical_spacing=0.08)
            fig.add_trace(go.Scatter(x=idx, y=s["prk"][-n:], name="Risk rank", line=dict(color="rgba(215,154,60,0.95)", width=1),
                                     fill="tozeroy", fillcolor="rgba(215,154,60,0.10)", hovertemplate="%{y:.0f} of 100"), 1, 1)
            for v in (100 / 3, 200 / 3):
                fig.add_hline(y=v, line=dict(color=tok_axis(), width=1, dash="dot"), row=1, col=1)
            fig.add_trace(go.Scatter(x=idx, y=100 * s["E"][-n:], name="Exposure", line=dict(color="rgba(76,125,240,0.9)", width=1, shape="hv"),
                                     fill="tozeroy", fillcolor="rgba(76,125,240,0.10)", hovertemplate="%{y:.0f}%"), 2, 1)
            fig.update_layout(**_fig(_TOK, chart_h))
            fig.update_xaxes(gridcolor=_TOK["grid"], zeroline=False, hoverformat=_date_fmt(intraday))
            fig.update_yaxes(gridcolor=_TOK["grid"], zeroline=False, side="right", range=[0, 100], tickvals=[0, 33, 67, 100], row=1, col=1)
            fig.update_yaxes(gridcolor=_TOK["grid"], zeroline=False, side="right", range=[0, 105], tickvals=[0, 50, 100], ticksuffix="%", row=2, col=1)
            _chart(fig)
    with right:
        with K.panel("levels", "Level ladder", context=f"every level the script draws, by price · distance in % and in {H}-bar σ",
                     help="Sorted by price around the close (marked). σ is the distance over one horizon's risk: a level at ±1σ is one "
                          "standard move away."):
            rows = [{"Level": k, "Price": _px(v, decimals), "From close": "—" if k == "Close" else _signed_pct(v / c - 1),
                     "σ": "—" if k == "Close" else fmt(math.log(v / c) / sH, "+0.00;-0.00")} for k, v in lv]
            close_row = next(i for i, (k, _) in enumerate(lv) if k == "Close")
            K.table(pd.DataFrame(rows), mark=close_row, align_left=("Level",), height=ladder_tbl,
                    tone={"From close": lambda x: None if x == "—" else "var(--long)" if x.startswith("+") else "var(--short)"})


# ═══ FORECAST ═══════════════════════════════════════════════════════════════
def forecast(e: dict, df: pd.DataFrame, tok: dict, decimals: int) -> None:
    _TOK.clear(); _TOK.update(tok)
    s, L, inp = e["series"], e["last"], e["inputs"]
    t = e["n"] - 1
    H = inp.H
    sig, c = s["sig"][t], float(df.close.iloc[-1])
    if _na(sig):
        K.note("The forecast needs a year of bars.")
        return
    hs = [L["h0"], H, L["h2"], L["h3"]]
    ups = [c * math.exp(s[f"qU{i}"][t] * sig * math.sqrt(h)) for i, h in enumerate(hs)]
    dns = [c * math.exp(-s[f"qD{i}"][t] * sig * math.sqrt(h)) for i, h in enumerate(hs)]
    # right column: term structure over stops; the fan takes the column's height
    term_h, stops_h = PANEL + _table_h(4), PANEL + _table_h(2)
    fan_h = term_h + GAP + stops_h - PANEL - PLOT_PAD
    left, right = st.columns(2, gap="small")
    with left:
        with K.panel("fan", "Forward ranges", context=f"where the close should be {fmt(inp.cover, '#')}% of the time · stops at {H} bars",
                     help="Each horizon's cone from today's close, joined into a fan. The dashed lines are the long and short stops, "
                          f"which hold for {H} bars."):
            back = min(80, t + 1)
            hist = df.close.iloc[-back:].to_numpy(float)
            fig = go.Figure()
            xs = [0] + hs
            fig.add_trace(go.Scatter(x=xs + xs[::-1], y=[c] + ups + dns[::-1] + [c], fill="toself", fillcolor="rgba(76,125,240,0.10)",
                                     line=dict(width=0), hoverinfo="skip", showlegend=False))
            tip = "%{customdata}<extra></extra>"
            cone = lambda side, vals: [f"Close · now<br>{_px(c, decimals)}"] + [
                f"{side} · in {h} bars<br>{_px(v, decimals)} ({_signed_pct(v / c - 1)})" for h, v in zip(hs, vals)]
            fig.add_trace(go.Scatter(x=xs, y=[c] + ups, mode="lines+markers", name="Cone", line=dict(color="rgba(76,125,240,0.85)", width=1),
                                     marker=dict(size=5), customdata=cone("High", ups), hovertemplate=tip))
            fig.add_trace(go.Scatter(x=xs, y=[c] + dns, mode="lines+markers", name="Cone", showlegend=False,
                                     line=dict(color="rgba(76,125,240,0.85)", width=1), marker=dict(size=5),
                                     customdata=cone("Low", dns), hovertemplate=tip))
            days = df.index[-back:]
            fig.add_trace(go.Scatter(x=list(range(-back + 1, 1)), y=hist, name="Close", line=dict(color=tok["ink"], width=1.3),
                                     customdata=[f"Close · {d.strftime(_date_fmt(_is_intraday(days)))}<br>{_px(v, decimals)}" for d, v in zip(days, hist)],
                                     hovertemplate=tip))
            for nm, px_, col in (("Short stop", s["stopS"][t], tok["candleUp"]), ("Long stop", s["stopL"][t], tok["candleDown"])):
                lab = f"{nm} · held {H} bars<br>{_px(px_, decimals)} ({_signed_pct(px_ / c - 1)})"
                fig.add_trace(go.Scatter(x=[0, H], y=[px_] * 2, mode="lines", name=nm, line=dict(color=col, width=1, dash="dash"),
                                         customdata=[lab, lab], hovertemplate=tip))
            for h, u_ in zip(hs, ups):
                fig.add_annotation(x=h, y=u_, text=f"{h}", showarrow=False, yshift=10, font=dict(size=9, color=tok["axis"]))
            fig.update_layout(**dict(_fig(tok, fan_h), hovermode="closest"))
            fig.update_xaxes(gridcolor=tok["grid"], zeroline=True, zerolinecolor=tok["grid"], title=dict(text="bars from now", font=dict(size=9)))
            fig.update_yaxes(gridcolor=tok["grid"], side="right", tickformat=",")
            _chart(fig)
    with right:
        with K.panel("term", "Term structure", context="each horizon's range, and how often it held on this chart",
                     help="Each horizon learns its own widths, so a longer one is not the shorter one scaled by the square root of time."):
            rows = []
            for i, h in enumerate(hs):
                ok = s[f"ok{i}"].astype(bool)
                n = int(ok.sum())
                held = 1 - float(s[f"mU{i}"][ok].mean() + s[f"mD{i}"][ok].mean()) if n else float("nan")
                rows.append({"Horizon": f"{h} bars", "Low": _px(dns[i], decimals), "High": _px(ups[i], decimals),
                             "Width": f_pct(math.log(ups[i] / dns[i]), "#.0"), "Held here": held, "Of": f"{n:,}"})
            K.table(pd.DataFrame(rows), align_left=("Horizon",), fmt={"Held here": lambda x: "—" if _na(x) else f"{100 * x:.1f}%"},
                    tone={"Held here": lambda x: None if _na(x) or abs(x - inp.cover / 100) <= 0.03 else "var(--caution)"})
        reg_now, tr_now = int(s["reg"][t]), int(s["trRaw"][t])
        regs = pd.Series(s["reg"]).shift(H).to_numpy()
        trs_ = pd.Series(np.where(np.isnan(s["T"]), np.nan, s["trRaw"])).shift(H).to_numpy()
        ok = s["settled"].astype(bool)
        rlab, tlab = ("calm", "normal", "stressed")[reg_now], ("down", "flat", "up")[tr_now]
        with K.panel("stops", "Stops", context=f"touched within {H} bars · target {fmt(inp.stop, '#')}% · here, and in today's {rlab} risk and {tlab} trend",
                     help="How often each stop was touched on this chart overall, and among forecasts made in the same risk regime and "
                          "trend state as today's."):
            rows = []
            for side, px_, hit in (("Long", s["stopL"][t], s["mS"]), ("Short", s["stopS"][t], s["mR"])):
                mr, mt = ok & (regs == reg_now), ok & (trs_ == tr_now)
                rows.append({"Stop": side, "Price": _px(px_, decimals), "Distance": f_pct(abs(px_ / c - 1), "#.00"),
                             "Touched": float(hit[ok].mean()) if ok.any() else float("nan"),
                             f"In {rlab} risk": float(hit[mr].mean()) if mr.any() else float("nan"),
                             f"In {tlab} trend": float(hit[mt].mean()) if mt.any() else float("nan")})
            pc = lambda x: "—" if _na(x) else f"{100 * x:.1f}%"
            off = lambda x: None if _na(x) or abs(x - inp.stop / 100) <= 0.03 else "var(--caution)"
            cols3 = ["Touched", f"In {rlab} risk", f"In {tlab} trend"]
            K.table(pd.DataFrame(rows), align_left=("Stop",), fmt={k: pc for k in cols3}, tone={k: off for k in cols3})

    st_now = int(s["st"][t])
    y, stv = s["yOut"], s["st"]
    prior = np.r_[np.full(H, -1), stv[:-H]] if len(stv) > H else np.full(len(stv), -1)
    scored = s["settled"].astype(bool) & ~np.isnan(y) & (prior >= 0)
    allv = y[scored]
    this = y[scored & (prior == st_now)] if st_now >= 0 else np.array([])
    stats_rows = 7
    hist_h = PANEL + _table_h(stats_rows) - PANEL - PLOT_PAD
    left, right = st.columns([1.6, 1], gap="small")
    with left:
        with K.panel("state", "What followed this state",
                     context=f"{st_name(st_now) if st_now >= 0 else 'no state yet'} · the next {H} bars, from the next open, in σ",
                     help="The distribution of what followed every past visit to today's state, against every state's. Pooled across "
                          "151 instruments no state had a reliable edge: read a difference here as this chart's history, not a forecast."):
            fig = go.Figure()
            xc, p_all, _, rng = _bins(allv, -6, 6, 0.5)
            p_this = _bins(this, -6, 6, 0.5)[1] if len(this) else None
            tips = [f"{_edge(lo)} to {_edge(hi)}σ<br>" + (f"This state {pt:.1%} · " if p_this is not None else "") + f"Every state {pa:.1%}"
                    for (lo, hi), pa, pt in zip(rng, p_all, p_this if p_this is not None else p_all)]
            fig.add_trace(go.Bar(x=xc, y=p_all, width=0.5, name=f"Every state · {len(allv):,}", marker=dict(color="rgba(139,149,166,0.35)", line=dict(width=0)),
                                 customdata=tips, hovertemplate="%{customdata}<extra></extra>"))
            if p_this is not None:
                fig.add_trace(go.Bar(x=xc, y=p_this, width=0.5, name=f"This state · {len(this):,}", marker=dict(color="rgba(76,125,240,0.65)", line=dict(width=0)),
                                     customdata=tips, hovertemplate="%{customdata}<extra></extra>"))
                fig.add_vline(x=float(np.mean(this)), line=dict(color="rgba(76,125,240,0.9)", width=1, dash="dot"))
            if len(allv):
                fig.add_vline(x=float(np.mean(allv)), line=dict(color=tok["axis"], width=1, dash="dot"))
            fig.update_layout(**dict(_fig(tok, hist_h), barmode="overlay", hovermode="closest"))
            fig.update_xaxes(gridcolor=tok["grid"], title=dict(text=f"next {H} bars, σ", font=dict(size=9)))
            fig.update_yaxes(gridcolor=tok["grid"], tickformat=".0%")
            _chart(fig)
    with right:
        z = s["lZ"][t]
        verdict = "too few to judge" if _na(z) else "proven positive" if z >= 2 else "proven negative" if z <= -2 else "unproven"
        stat = lambda f, v: "—" if len(v) == 0 else f(v)
        rows = [{"": "Samples", "This state": f"{len(this):,}", "Every state": f"{len(allv):,}"},
                {"": "Independent", "This state": fmt(s["lNe"][t], "#"), "Every state": "—"},
                {"": "Mean (σ)", "This state": stat(lambda v: _sg(np.mean(v)), this), "Every state": stat(lambda v: _sg(np.mean(v)), allv)},
                {"": "Median (σ)", "This state": stat(lambda v: _sg(np.median(v)), this), "Every state": stat(lambda v: _sg(np.median(v)), allv)},
                {"": "Ended higher", "This state": stat(lambda v: f"{100 * np.mean(v > 0):.0f}%", this), "Every state": stat(lambda v: f"{100 * np.mean(v > 0):.0f}%", allv)},
                {"": "Spread (σ)", "This state": stat(lambda v: f"{np.std(v):.2f}", this), "Every state": stat(lambda v: f"{np.std(v):.2f}", allv)},
                {"": "Verdict", "This state": verdict, "Every state": "—"}]
        with K.panel("statestats", "This state against every state", context=f"the next {H} bars, in σ",
                     help="A state is proven when its shrunk edge is at least 2 standard errors from the chart's usual outcome."):
            K.table(pd.DataFrame(rows), align_left=("",))


# ═══ AUDIT ══════════════════════════════════════════════════════════════════
def audit(e: dict, df: pd.DataFrame, tok: dict) -> None:
    _TOK.clear(); _TOK.update(tok)
    s, L, inp = e["series"], e["last"], e["inputs"]
    nF = L["nF"]
    off = lambda v, tgt: "warning" if (not _na(v) and abs(v - tgt) > 0.03) else "neutral"
    ls = L["nMS"] / nF if nF else float("nan")
    rs = L["nMR"] / nF if nF else float("nan")
    K.kpi_strip([
        dict(label="Cone held", value=f_pct(L["cov"], "#.0"), tone=off(L["cov"], inp.cover / 100),
             subtext=f"target {fmt(inp.cover, '#')}% · last 250 {f_pct(s['covRecent'][-1], '#.0')}"),
        dict(label="Long stop touched", value=f_pct(ls, "#.0"), tone=off(ls, inp.stop / 100), subtext=f"target {fmt(inp.stop, '#')}%"),
        dict(label="Short stop touched", value=f_pct(rs, "#.0"), tone=off(rs, inp.stop / 100), subtext=f"target {fmt(inp.stop, '#')}%"),
        dict(label="Sharpe · exposure", value=fmt(L["shF"], "0.00"), subtext=f"buy and hold {fmt(L['shH'], '0.00')}",
             tone="success" if (not _na(L["shF"]) and not _na(L["shH"]) and L["shF"] >= L["shH"]) else "neutral"),
        dict(label="Max drawdown", value=f_pct(L["ddF"], "#.0"), subtext=f"buy and hold {f_pct(L['ddH'], '#.0')}",
             tone="success" if L["ddF"] > L["ddH"] else "neutral"),
    ], key="kpi-audit", max_cols=5)

    pct = lambda x: "—" if _na(x) else f"{100 * x:.1f}%"
    tgt = lambda v: (lambda x: None if _na(x) or abs(x - v) <= 0.03 else "var(--caution)")
    left, right = st.columns(2, gap="small")
    with left:
        with K.panel("cal-h", "By horizon", context=f"every settled forecast · target {fmt(inp.cover, '#')}% inside, {fmt((100 - inp.cover) / 2, '#')}% each side",
                     help="How often each horizon's cone held on this chart, and which side it missed on. Amber: more than 3 points off."):
            rows = []
            for i, h in enumerate([L["h0"], inp.H, L["h2"], L["h3"]]):
                ok = s[f"ok{i}"].astype(bool)
                n = int(ok.sum())
                up = float(s[f"mU{i}"][ok].mean()) if n else float("nan")
                dn = float(s[f"mD{i}"][ok].mean()) if n else float("nan")
                rows.append({"Horizon": f"{h} bars", "Settled": f"{n:,}", "Inside": 1 - up - dn if n else float("nan"), "Above": up, "Below": dn})
            K.table(pd.DataFrame(rows), fmt={c: pct for c in ("Inside", "Above", "Below")}, align_left=("Horizon",),
                    tone={"Inside": tgt(inp.cover / 100)}, height=_table_h(6))          # meets the six-row table beside it
    with right:
        with K.panel("cal-s", "By risk regime and trend", context="the state each forecast was made in",
                     help="The cone and the stops learn their widths per risk regime and per trend state, so each row should sit near its "
                          "target. Amber: more than 3 points off."):
            reg = pd.Series(s["reg"]).shift(inp.H).to_numpy()
            trs = pd.Series(np.where(np.isnan(s["T"]), np.nan, s["trRaw"])).shift(inp.H).to_numpy()
            ok = s["settled"].astype(bool)
            inside = ~(s["mU"] | s["mD"])
            by = []
            for name, key, vals in (("Risk", reg, ("calm", "normal", "stressed")), ("Trend", trs, ("down", "flat", "up"))):
                for g, lab in enumerate(vals):
                    m = ok & (key == g)
                    n = int(m.sum())
                    by.append({"By": name, "State": lab, "Forecasts": f"{n:,}", "Cone held": float(inside[m].mean()) if n else float("nan"),
                               "Long stop": float(s["mS"][m].mean()) if n else float("nan"),
                               "Short stop": float(s["mR"][m].mean()) if n else float("nan")})
            K.table(pd.DataFrame(by), fmt={c: pct for c in ("Cone held", "Long stop", "Short stop")}, align_left=("By", "State"),
                    tone={"Cone held": tgt(inp.cover / 100), "Long stop": tgt(inp.stop / 100), "Short stop": tgt(inp.stop / 100)})
    x = s["x1"][s["settled"].astype(bool)]
    x = x[~np.isnan(x)]
    left, right = st.columns(2, gap="small")
    with left:
        with K.panel("cal-x", "Surprises, in band widths",
                     context=f"beyond +1 {f_pct(float((x > 1).mean()) if len(x) else float('nan'), '#.0')} · beyond −1 "
                             f"{f_pct(float((x < -1).mean()) if len(x) else float('nan'), '#.0')} · target {fmt((100 - inp.cover) / 2, '#')}% each",
                     help=f"Each {inp.H}-bar surprise over the band it was judged against: beyond ±1 is a miss. Bunched near 0, the "
                          "forecasts were too wide; piled past ±1, too narrow."):
            xc, share, cnt, rng = _bins(np.clip(x, -3, 3), -3, 3, 0.125)
            lab = lambda lo, hi: (f"below {_edge(hi)}" if lo <= -3 else f"above {_edge(lo)}" if hi >= 3 else f"{_edge(lo)} to {_edge(hi)}")
            fig = go.Figure(go.Bar(x=xc, y=share, width=0.125, marker=dict(color="rgba(139,149,166,0.45)", line=dict(width=0)),
                                   customdata=[f"{lab(lo, hi)} band widths<br>{p_:.1%} of surprises · {k:,}" for (lo, hi), p_, k in zip(rng, share, cnt)],
                                   hovertemplate="%{customdata}<extra></extra>"))
            for v in (-1, 1):
                fig.add_vline(x=v, line=dict(color="rgba(215,154,60,0.9)", width=1, dash="dot"))
            fig.update_layout(**dict(_fig(tok, 300), hovermode="closest", showlegend=False))
            fig.update_xaxes(gridcolor=tok["grid"], tickvals=[-3, -2, -1, 0, 1, 2, 3])
            fig.update_yaxes(gridcolor=tok["grid"], tickformat=".0%", side="right")
            _chart(fig)
    with right:
        with K.panel("proof-chart", "Exposure against buy and hold",
                     context=f"CAGR {f_pct(L['cagF'], '#.0')} against {f_pct(L['cagH'], '#.0')} · log %, net of costs",
                     help=f"{L['nP']:,} bars over {fmt(L['yrs'], '0.0')} years, one bar late, {fmt(inp.cost, '#')} bp per unit of change. "
                          "Exposure held is beneath. The dial's job is the drawdown, not the return."):
            idx = df.index[-len(s["eqF"]):]
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.72, 0.28], vertical_spacing=0.06)
            lh, lf = 100 * np.log(s["eqH"]), 100 * np.log(s["eqF"])
            fig.add_trace(go.Scatter(x=idx, y=lh, name="Buy and hold", line=dict(color=tok["axis"], width=1),
                                     customdata=[_sg(v, ".1f") + "%" for v in lh], hovertemplate="%{customdata}"), 1, 1)
            fig.add_trace(go.Scatter(x=idx, y=lf, name="Following exposure", line=dict(color=tok["ink"], width=1.5),
                                     customdata=[_sg(v, ".1f") + "%" for v in lf], hovertemplate="%{customdata}"), 1, 1)
            fig.add_trace(go.Scatter(x=idx, y=100 * s["E"], name="Exposure", line=dict(color="rgba(76,125,240,0.85)", width=1, shape="hv"),
                                     fill="tozeroy", fillcolor="rgba(76,125,240,0.10)", hovertemplate="%{y:.0f}%"), 2, 1)
            fig.update_layout(**_fig(tok, 300))
            fig.update_xaxes(gridcolor=tok["grid"], zeroline=False, hoverformat=_date_fmt(_is_intraday(idx)))
            fig.update_yaxes(gridcolor=tok["grid"], zeroline=False, side="right", ticksuffix="%", row=1, col=1)
            fig.update_yaxes(gridcolor=tok["grid"], zeroline=False, side="right", range=[0, 105], tickvals=[0, 50, 100], ticksuffix="%", row=2, col=1)
            _chart(fig)
    _ledger(e)


def _ledger(e: dict) -> None:
    L, inp = e["last"], e["inputs"]
    gN, gM, gQ, H_ = L["gN"], L["gM"], L["gQ"], inp.H
    cur = int(e["series"]["st"][-1])
    rows = []
    for r in e["ledger"]:
        ne, mu = r["n_eff"], r["mean"]
        z = edge = post = float("nan")
        if ne >= 5 and gN > 30 * H_ and gN > 1:
            se2 = gQ / (gN - 1) / ne
            shr = inp.tau ** 2 / (inp.tau ** 2 + se2)
            edge = mu - gM
            post = shr * edge
            z = edge * math.sqrt(shr / se2)
        verdict = "too few" if _na(z) else "proven positive" if z >= 2 else "proven negative" if z <= -2 else "unproven"
        rows.append({"Trend": r["trend"], "Close": r["close"], "Seen": r["n"], "Independent": ne,
                     f"Next {H_} bars (σ)": mu, "Against usual (σ)": edge, "Shrunk edge (σ)": post, "z": z, "Verdict": verdict})
    df = pd.DataFrame(rows)
    with K.panel("ledger", "Ledger", context=f"nine states · scored {H_} bars later from the next open · usual {fmt(gM, '+0.00;-0.00')}σ over {gN:,} samples",
                 meta=f"believable edge τ = {inp.tau}",
                 help="A state is proven when its shrunk edge is at least 2 standard errors from the chart's usual outcome. Samples count "
                      "as independent only when their signal bars are at least one horizon apart. The marked row is the state now."):
        num = lambda x: _sg(x)
        vtone = lambda v: "var(--long)" if v == "proven positive" else "var(--short)" if v == "proven negative" else None
        K.table(df, fmt={c: num for c in df.columns if "σ" in c or c == "z"}, tone={"Verdict": vtone},
                mark=cur if cur >= 0 else None, align_left=("Trend", "Close", "Verdict"))


# ═══ EVENTS ═════════════════════════════════════════════════════════════════
def events(e: dict, df: pd.DataFrame, intraday: bool, decimals: int) -> None:
    idx = df.index[-e["n"]:]
    close = df.close.to_numpy(float)[-e["n"]:]
    ev = []
    for title, arr in e["alerts"].items():
        cat = CATEGORY[title.split(" · ")[0]]
        for i in np.flatnonzero(np.asarray(arr, dtype=bool)):
            ev.append((idx[i], cat, title, close[i]))
    counts = {c: sum(1 for x in ev if x[1] == c) for c in dict.fromkeys(CATEGORY.values())}
    opts = [c for c in counts if counts[c]]
    default = [c for c in opts if c not in ("Misses", "Midline")] or opts
    with K.panel("events", "Events", context="every alert condition the script defines, as it fired on this chart's closed bars",
                 meta=f"{len(ev):,} in all",
                 help="Titles and messages are the script's alertcondition() text; none of them is a trade signal. Misses and midline "
                      "crosses are frequent by design, so they start hidden. The latest 300 are listed."):
        with st.container(key="eventfilter"):
            pick = st.pills("Show", opts, selection_mode="multi", default=default, key="ev_pick", label_visibility="collapsed",
                            format_func=lambda c: f"{c} · {counts[c]:,}")
        keep = sorted((x for x in ev if x[1] in (pick or [])), key=lambda x: x[0], reverse=True)
        rows = [{"Time": _stamp(t_, intraday), "Kind": cat, "Event": title, "Close": _px(px_, decimals), "What it means": ALERT_TEXT[title]}
                for t_, cat, title, px_ in keep[:300]]
        if rows:
            K.table(pd.DataFrame(rows), align_left=("Time", "Kind", "Event", "What it means"))
