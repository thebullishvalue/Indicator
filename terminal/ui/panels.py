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


def _na(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


def _stamp(ts, intraday: bool) -> str:
    return ts.strftime("%Y-%m-%d %H:%M" if intraday else "%Y-%m-%d")


def _px(x, dec):
    return "—" if _na(x) else f"{x:,.{dec}f}"


def _signed_pct(x, dec: int = 2) -> str:
    return "—" if _na(x) else f"{100 * x:+.{dec}f}%"


def _fig(tok: dict, height: int) -> dict:
    return dict(height=height, margin=dict(l=16, r=16, t=8, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono, monospace", size=10, color=tok["axis"]), hovermode="x unified",
                legend=dict(orientation="h", y=1.08, x=0, bgcolor="rgba(0,0,0,0)"))


def _chart(fig) -> None:
    st.plotly_chart(fig, width="stretch", config=dict(displayModeBar=False))


def _units(u: float) -> str:
    if _na(u):
        return "—"
    return f"{u:,.0f}" if u >= 100 else f"{u:,.2f}" if u >= 1 else f"{u:,.4f}"


# ═══ PLAN ═══════════════════════════════════════════════════════════════════
def plan(e: dict, vp: dict, df: pd.DataFrame, decimals: int, currency: str, intraday: bool) -> None:
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

    left, right = st.columns(2, gap="small")
    with left:
        with K.panel("size", "Position size", context="sized to lose a set share of equity at the script's stops"):
            with st.container(key="sizeinputs"):
                a, b = st.columns(2, gap="small")
                equity = a.number_input(f"Equity · {currency}" if currency else "Equity", min_value=0.0, value=1_000_000.0,
                                        step=10_000.0, format="%.0f", key="equity")
                risk = b.number_input("Risk per trade · %", min_value=0.05, max_value=10.0, value=float(inp.risk), step=0.05,
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
            K.note(f"Each stop is touched within {H} bars {fmt(inp.stop, '#')}% of the time. Above 100% of equity a size needs leverage. "
                   "The exposure row is the position the dial says to hold, before any stop.")
    with right:
        with K.panel("levels", "Level ladder", context=f"every level the script draws, by price · distance in % and in {H}-bar σ"):
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
            rows = [{"Level": k, "Price": _px(v, decimals), "From close": "—" if k == "Close" else _signed_pct(v / c - 1),
                     "σ": "—" if k == "Close" else fmt(math.log(v / c) / sH, "+0.00;-0.00")} for k, v in lv]
            close_row = next(i for i, (k, _) in enumerate(lv) if k == "Close")
            K.table(pd.DataFrame(rows), mark=close_row, align_left=("Level",),
                    tone={"From close": lambda x: None if x == "—" else "var(--long)" if x.startswith("+") else "var(--short)"})


# ═══ FORECAST ═══════════════════════════════════════════════════════════════
def forecast(e: dict, df: pd.DataFrame, tok: dict, decimals: int) -> None:
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
    left, right = st.columns(2, gap="small")
    with left:
        with K.panel("fan", "Forward ranges", context=f"where the close should be {fmt(inp.cover, '#')}% of the time · stops at {H} bars"):
            back = min(80, t + 1)
            hist = df.close.iloc[-back:].to_numpy(float)
            fig = go.Figure()
            xs = [0] + hs
            fig.add_trace(go.Scatter(x=xs + xs[::-1], y=[c] + ups + dns[::-1] + [c], fill="toself", fillcolor="rgba(76,125,240,0.10)",
                                     line=dict(width=0), hoverinfo="skip", showlegend=False))
            fig.add_trace(go.Scatter(x=xs, y=[c] + ups, mode="lines+markers", name="Cone", line=dict(color="rgba(76,125,240,0.85)", width=1),
                                     marker=dict(size=5)))
            fig.add_trace(go.Scatter(x=xs, y=[c] + dns, mode="lines+markers", name="Cone", showlegend=False,
                                     line=dict(color="rgba(76,125,240,0.85)", width=1), marker=dict(size=5)))
            fig.add_trace(go.Scatter(x=list(range(-back + 1, 1)), y=hist, name="Close", line=dict(color=tok["ink"], width=1.3)))
            fig.add_trace(go.Scatter(x=[0, H], y=[s["stopS"][t]] * 2, mode="lines", name="Short stop", line=dict(color=tok["candleUp"], width=1, dash="dash")))
            fig.add_trace(go.Scatter(x=[0, H], y=[s["stopL"][t]] * 2, mode="lines", name="Long stop", line=dict(color=tok["candleDown"], width=1, dash="dash")))
            for h, u_ in zip(hs, ups):
                fig.add_annotation(x=h, y=u_, text=f"{h}", showarrow=False, yshift=10, font=dict(size=9, color=tok["axis"]))
            fig.update_layout(**dict(_fig(tok, 320), hovermode="closest"))
            fig.update_xaxes(gridcolor=tok["grid"], zeroline=True, zerolinecolor=tok["grid"], title=dict(text="bars from now", font=dict(size=9)))
            fig.update_yaxes(gridcolor=tok["grid"], side="right")
            _chart(fig)
    with right:
        with K.panel("term", "Term structure", context="each horizon's range, and how often it held on this chart"):
            rows = []
            for i, h in enumerate(hs):
                ok = s[f"ok{i}"].astype(bool)
                n = int(ok.sum())
                held = 1 - float(s[f"mU{i}"][ok].mean() + s[f"mD{i}"][ok].mean()) if n else float("nan")
                rows.append({"Horizon": f"{h} bars", "Low": _px(dns[i], decimals), "High": _px(ups[i], decimals),
                             "Width": f_pct(math.log(ups[i] / dns[i]), "#.0"), "Held here": held, "Of": f"{n:,}"})
            K.table(pd.DataFrame(rows), align_left=("Horizon",), fmt={"Held here": lambda x: "—" if _na(x) else f"{100 * x:.1f}%"},
                    tone={"Held here": lambda x: None if _na(x) or abs(x - inp.cover / 100) <= 0.03 else "var(--caution)"})
            K.note("Each horizon learns its own widths, so a longer one is not the shorter one scaled by the square root of time.")

    st_now = int(s["st"][t])
    y, stv = s["yOut"], s["st"]
    prior = np.r_[np.full(H, -1), stv[:-H]] if len(stv) > H else np.full(len(stv), -1)
    scored = s["settled"].astype(bool) & ~np.isnan(y) & (prior >= 0)
    allv = y[scored]
    this = y[scored & (prior == st_now)] if st_now >= 0 else np.array([])
    with K.panel("state", "What followed this state",
                 context=f"{st_name(st_now) if st_now >= 0 else 'no state yet'} · the next {H} bars, from the next open, in σ"):
        if len(this) >= 5:
            fig = go.Figure()
            bins = dict(start=-6, end=6, size=0.5)
            fig.add_trace(go.Histogram(x=allv, xbins=bins, histnorm="probability", name=f"Every state · {len(allv):,}",
                                       marker=dict(color="rgba(139,149,166,0.35)")))
            fig.add_trace(go.Histogram(x=this, xbins=bins, histnorm="probability", name=f"This state · {len(this):,}",
                                       marker=dict(color="rgba(76,125,240,0.65)")))
            fig.add_vline(x=float(np.mean(allv)), line=dict(color=tok["axis"], width=1, dash="dot"))
            fig.add_vline(x=float(np.mean(this)), line=dict(color="rgba(76,125,240,0.9)", width=1, dash="dot"))
            fig.update_layout(**dict(_fig(tok, 240), barmode="overlay", hovermode="x"))
            fig.update_xaxes(gridcolor=tok["grid"], title=dict(text=f"next {H} bars, σ", font=dict(size=9)))
            fig.update_yaxes(gridcolor=tok["grid"], tickformat=".0%")
            _chart(fig)
            z = s["lZ"][t]
            verdict = "too few to judge" if _na(z) else "proven positive" if z >= 2 else "proven negative" if z <= -2 else "unproven"
            K.note(f"This state: {len(this):,} samples ({fmt(s['lNe'][t], '#')} independent), mean {fmt(float(np.mean(this)), '+0.00;-0.00')}σ "
                   f"against {fmt(float(np.mean(allv)), '+0.00;-0.00')}σ for every state: {verdict}. Pooled across 151 instruments no state had "
                   "a reliable edge, so read a difference here as this chart's history, not a forecast.")
        else:
            K.note("Too few samples of this state on this chart to draw its outcomes.")


# ═══ AUDIT ══════════════════════════════════════════════════════════════════
def audit(e: dict, df: pd.DataFrame, tok: dict) -> None:
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
        with K.panel("cal-h", "By horizon", context=f"every settled forecast · target {fmt(inp.cover, '#')}% inside, {fmt((100 - inp.cover) / 2, '#')}% each side"):
            rows = []
            for i, h in enumerate([L["h0"], inp.H, L["h2"], L["h3"]]):
                ok = s[f"ok{i}"].astype(bool)
                n = int(ok.sum())
                up = float(s[f"mU{i}"][ok].mean()) if n else float("nan")
                dn = float(s[f"mD{i}"][ok].mean()) if n else float("nan")
                rows.append({"Horizon": f"{h} bars", "Settled": f"{n:,}", "Inside": 1 - up - dn if n else float("nan"), "Above": up, "Below": dn})
            K.table(pd.DataFrame(rows), fmt={c: pct for c in ("Inside", "Above", "Below")}, align_left=("Horizon",),
                    tone={"Inside": tgt(inp.cover / 100)})
        with K.panel("cal-x", "Surprises, in band widths", context=f"each {inp.H}-bar surprise over the band it was judged against · beyond ±1 is a miss"):
            x = s["x1"][s["settled"].astype(bool)]
            x = x[~np.isnan(x)]
            if len(x):
                fig = go.Figure(go.Histogram(x=np.clip(x, -3, 3), xbins=dict(start=-3, end=3.0001, size=0.125), histnorm="probability",
                                             marker=dict(color="rgba(139,149,166,0.45)")))
                for v in (-1, 1):
                    fig.add_vline(x=v, line=dict(color="rgba(215,154,60,0.9)", width=1, dash="dot"))
                fig.update_layout(**dict(_fig(tok, 220), hovermode="x", showlegend=False))
                fig.update_xaxes(gridcolor=tok["grid"], tickvals=[-3, -2, -1, 0, 1, 2, 3])
                fig.update_yaxes(gridcolor=tok["grid"], tickformat=".0%")
                _chart(fig)
                K.note(f"Beyond +1: {f_pct(float((x > 1).mean()), '#.0')}, beyond −1: {f_pct(float((x < -1).mean()), '#.0')} "
                       f"(target {fmt((100 - inp.cover) / 2, '#')}% each). Bunched near 0, the forecasts were too wide; piled past ±1, too narrow.")
    with right:
        with K.panel("cal-s", "By risk regime and trend", context="the state each forecast was made in · amber: more than 3 points off"):
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
        with K.panel("proof-chart", "Exposure against buy and hold", context="growth, log %, net of costs · exposure held, beneath"):
            idx = df.index[-len(s["eqF"]):]
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.72, 0.28], vertical_spacing=0.05)
            fig.add_trace(go.Scatter(x=idx, y=100 * np.log(s["eqH"]), name="Buy and hold", line=dict(color=tok["axis"], width=1)), 1, 1)
            fig.add_trace(go.Scatter(x=idx, y=100 * np.log(s["eqF"]), name="Following exposure", line=dict(color=tok["ink"], width=1.5)), 1, 1)
            fig.add_trace(go.Scatter(x=idx, y=100 * s["E"], name="Exposure", line=dict(color="rgba(76,125,240,0.85)", width=1, shape="hv"),
                                     fill="tozeroy", fillcolor="rgba(76,125,240,0.10)"), 2, 1)
            fig.update_layout(**_fig(tok, 300))
            fig.update_xaxes(gridcolor=tok["grid"], zeroline=False)
            fig.update_yaxes(gridcolor=tok["grid"], zeroline=False, side="right", ticksuffix="%", row=1, col=1)
            fig.update_yaxes(gridcolor=tok["grid"], zeroline=False, side="right", range=[0, 105], tickvals=[0, 50, 100], ticksuffix="%", row=2, col=1)
            _chart(fig)
            K.note(f"{L['nP']:,} bars over {fmt(L['yrs'], '0.0')} years, one bar late, {fmt(inp.cost, '#')} bp per unit of change. "
                   f"CAGR {f_pct(L['cagF'], '#.0')} against {f_pct(L['cagH'], '#.0')}. The dial's job is the drawdown, not the return.")
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
                 meta=f"believable edge τ = {inp.tau}"):
        num = lambda x: "—" if _na(x) else f"{x:+.2f}"
        vtone = lambda v: "var(--long)" if v == "proven positive" else "var(--short)" if v == "proven negative" else None
        K.table(df, fmt={c: num for c in df.columns if "σ" in c or c == "z"}, tone={"Verdict": vtone},
                mark=cur if cur >= 0 else None, align_left=("Trend", "Close", "Verdict"))
        K.note("A state is proven when its shrunk edge is at least 2 standard errors from the chart's usual outcome. Samples count as "
               "independent only when their signal bars are at least one horizon apart. The marked row is the state now.")


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
                 meta=f"{len(ev):,} in all"):
        with st.container(key="eventfilter"):
            pick = st.pills("Show", opts, selection_mode="multi", default=default, key="ev_pick", label_visibility="collapsed",
                            format_func=lambda c: f"{c} · {counts[c]:,}")
        keep = sorted((x for x in ev if x[1] in (pick or [])), key=lambda x: x[0], reverse=True)
        rows = [{"Time": _stamp(t_, intraday), "Kind": cat, "Event": title, "Close": _px(px_, decimals), "What it means": ALERT_TEXT[title]}
                for t_, cat, title, px_ in keep[:300]]
        if rows:
            K.table(pd.DataFrame(rows), align_left=("Time", "Kind", "Event", "What it means"))
        K.note("Titles and messages are the script's alertcondition() text; none of them is a trade signal. Misses and midline crosses "
               "are frequent by design, so they start hidden. The latest 300 are listed.")
