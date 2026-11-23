"""The bottom panel: the script's source, its proof (a strategy report), the ledger's nine states, the calibration
record, the alert log and the data window - everything the script keeps, laid out the way a terminal keeps it."""
from __future__ import annotations

import html as H
import math
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engine.table import f_pct, fmt
from ui import components as K

PINE = Path(__file__).resolve().parents[2] / "pramana.pine"

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


def _na(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


def _stamp(ts, intraday: bool) -> str:
    return ts.strftime("%Y-%m-%d %H:%M" if intraday else "%Y-%m-%d")


def pine_editor() -> None:
    src = PINE.read_text(encoding="utf-8")
    with K.panel("pine", "pramana.pine", context=f"Pine Script v6 · {len(src.splitlines()):,} lines · read only",
                 meta="the script this terminal runs, ported to Python"):
        st.code(src, language="javascript", line_numbers=True, height=520)


def proof(e: dict, df: pd.DataFrame, tok: dict, dark: bool, intraday: bool) -> None:
    s, L = e["series"], e["last"]
    items = [
        dict(label="Sharpe · exposure", value=fmt(L["shF"], "0.00"), subtext=f"buy and hold {fmt(L['shH'], '0.00')}",
             tone="success" if (not _na(L["shF"]) and not _na(L["shH"]) and L["shF"] >= L["shH"]) else "neutral",
             tooltip="Following exposure against buy and hold on this chart, one bar late, net of costs. Annualised by this chart's bars per year."),
        dict(label="Max drawdown", value=f_pct(L["ddF"], "#.0"), subtext=f"buy and hold {f_pct(L['ddH'], '#.0')}",
             tone="success" if L["ddF"] > L["ddH"] else "neutral"),
        dict(label="CAGR · exposure", value=f_pct(L["cagF"], "#.0"), subtext=f"buy and hold {f_pct(L['cagH'], '#.0')}"),
        dict(label="Exposure now", value=f_pct(s["E"][-1], "#"), subtext=f"dial {f_pct(s['dial'][-1], '#')}"),
        dict(label="Record", value=f"{L['nP']:,} bars", subtext=f"{fmt(L['yrs'], '0.0')} years · {fmt(L['bpy'], '#')} bars a year"),
        dict(label="Midline rule", value=fmt(L["shM"], "0.00"), subtext=f"{L['mRuns']} runs · {f_pct(L['mWon'] / L['mRuns'] if L['mRuns'] else float('nan'), '#')} won",
             tooltip="Long above the midline, flat below, scored as the exposure is. A description, not a signal."),
    ]
    K.kpi_strip(items, key="kpi-proof")
    with K.panel("proof-chart", "Growth", context="log %, net of costs · exposure against buy and hold"):
        idx = df.index[-len(s["eqF"]):]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=idx, y=100 * np.log(s["eqH"]), name="Buy and hold", line=dict(color=tok["axis"], width=1)))
        fig.add_trace(go.Scatter(x=idx, y=100 * np.log(s["eqF"]), name="Following exposure", line=dict(color=tok["ink"], width=1.6)))
        fig.add_trace(go.Scatter(x=idx, y=100 * s["E"], name="Exposure (%)", yaxis="y2", line=dict(color="rgba(76,125,240,0.55)", width=1),
                                 fill="tozeroy", fillcolor="rgba(76,125,240,0.07)"))
        fig.update_layout(height=320, margin=dict(l=8, r=8, t=8, b=8), paper_bgcolor=tok["bg"], plot_bgcolor=tok["bg"],
                          font=dict(family="JetBrains Mono, monospace", size=10, color=tok["axis"]), hovermode="x unified",
                          legend=dict(orientation="h", y=1.08, x=0, bgcolor="rgba(0,0,0,0)"),
                          xaxis=dict(gridcolor=tok["grid"], showline=False),
                          yaxis=dict(gridcolor=tok["grid"], title="log %", side="right"),
                          yaxis2=dict(overlaying="y", side="left", range=[0, 400], showgrid=False, title="exposure %", tickvals=[0, 50, 100]))
        st.plotly_chart(fig, width="stretch", config=dict(displayModeBar=False))


def ledger(e: dict) -> None:
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
        rows.append({"": "▶" if r["state"] == cur else "", "Trend": r["trend"], "Close": r["close"], "Seen": r["n"], "Independent": ne,
                     f"Next {H_} bars (σ)": mu, "Against usual (σ)": edge, "Shrunk edge (σ)": post, "z": z, "Verdict": verdict})
    df = pd.DataFrame(rows)
    with K.panel("ledger", "Ledger", context=f"nine states · scored {H_} bars later from the next open · usual {fmt(gM, '+0.00;-0.00')}σ over {gN:,} samples",
                 meta=f"believable edge τ = {inp.tau}"):
        cur_row = next((i for i, r in enumerate(e["ledger"]) if r["state"] == cur), None)
        num = lambda x: "—" if _na(x) else f"{x:+.2f}"
        vtone = lambda v: "var(--long)" if v == "proven positive" else "var(--short)" if v == "proven negative" else None
        K.table(df.drop(columns=[""]), fmt={c: num for c in df.columns if "σ" in c or c == "z"},
                tone={"Verdict": vtone}, mark=cur_row, align_left=("Trend", "Close", "Verdict"))
        K.note("A state is proven when its shrunk edge is at least 2 standard errors from the chart's usual outcome. "
               "Samples count as independent only when their signal bars are at least one horizon apart. Pooled across 151 "
               "instruments no state had a reliable edge, so expect most states to read unproven.")


def record(e: dict) -> None:
    s, L, inp = e["series"], e["last"], e["inputs"]
    H_ = inp.H
    a = (1 - inp.cover / 100) / 2
    rungs = [L["h0"], H_, L["h2"], L["h3"]]
    rows = []
    for i, h in enumerate(rungs):
        ok = s[f"ok{i}"].astype(bool)
        n = int(ok.sum())
        up = float(s[f"mU{i}"][ok].mean()) if n else float("nan")
        dn = float(s[f"mD{i}"][ok].mean()) if n else float("nan")
        rows.append({"Rung": f"{h} bars", "Settled": n, "Inside": 1 - up - dn if n else float("nan"), "Above": up, "Below": dn,
                     "Target inside": inp.cover / 100, "Target each side": a})
    with K.panel("record", "Calibration record", context=f"every settled forecast on this chart · cone target {fmt(inp.cover, '#')}% · stop target {fmt(inp.stop, '#')}%"):
        pct = lambda x: "—" if _na(x) else f"{100 * x:.1f}%"
        K.table(pd.DataFrame(rows), fmt={c: pct for c in ("Inside", "Above", "Below", "Target inside", "Target each side")},
                tone={"Inside": lambda x: None if _na(x) or abs(x - inp.cover / 100) <= 0.03 else "var(--caution)"}, align_left=("Rung",))
        reg = pd.Series(s["reg"]).shift(H_).to_numpy()
        trs = pd.Series(np.where(np.isnan(s["T"]), np.nan, s["trRaw"])).shift(H_).to_numpy()
        ok = s["settled"].astype(bool)
        inside = ~(s["mU"] | s["mD"])
        by = []
        for name, key, vals in (("Risk regime", reg, ("calm", "normal", "stressed")), ("Trend state", trs, ("down", "flat", "up"))):
            for g, lab in enumerate(vals):
                m = ok & (key == g)
                n = int(m.sum())
                by.append({"By": name, "State": lab, "Forecasts": n,
                           "Cone held": float(inside[m].mean()) if n else float("nan"),
                           "Long stop touched": float(s["mS"][m].mean()) if n else float("nan"),
                           "Short stop touched": float(s["mR"][m].mean()) if n else float("nan")})
        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
        off = lambda tgt: (lambda x: None if _na(x) or abs(x - tgt) <= 0.03 else "var(--caution)")
        K.table(pd.DataFrame(by), fmt={c: pct for c in ("Cone held", "Long stop touched", "Short stop touched")},
                tone={"Cone held": off(inp.cover / 100), "Long stop touched": off(inp.stop / 100), "Short stop touched": off(inp.stop / 100)},
                align_left=("By", "State"))
        K.note("Amber marks a row more than 3 points off its target. " + f"Overall the cone held {f_pct(L['cov'], '#.0')} of {L['nF']:,} forecasts (last 250: {f_pct(s['covRecent'][-1], '#.0')}); "
               f"the long stop was touched {f_pct(L['nMS'] / L['nF'] if L['nF'] else float('nan'), '#.0')} of the time and the short stop "
               f"{f_pct(L['nMR'] / L['nF'] if L['nF'] else float('nan'), '#.0')}. The widths learn per risk regime and per trend state, "
               "so each row should sit near its target - that is what the adaptation is for.")


def alerts(e: dict, df: pd.DataFrame, name: str, tf: str, intraday: bool) -> None:
    ev = []
    idx = df.index[-e["n"]:]
    for title, arr in e["alerts"].items():
        for i in np.flatnonzero(np.asarray(arr, dtype=bool)):
            ev.append((idx[i], title))
    ev.sort(key=lambda x: x[0], reverse=True)
    rows = [{"Time": _stamp(t, intraday), "Alert": title, "Message": f"{name} {tf} · {ALERT_TEXT[title]}"} for t, title in ev[:400]]
    with K.panel("alerts", "Alert log", context="every alert condition the script defines, as it fired on this chart's closed bars",
                 meta=f"{len(ev):,} fired"):
        if rows:
            K.table(pd.DataFrame(rows[:200]), align_left=("Time", "Alert", "Message"))
        K.note("Titles and messages are the script's alertcondition() text. None of them is a trade signal, and the wording says so.")


def data_window(e: dict, vp: dict, df: pd.DataFrame, decimals: int, intraday: bool) -> None:
    s, H_ = e["series"], e["inputs"].H
    t = e["n"] - 1
    px = lambda x: "—" if _na(x) else f"{x:,.{decimals}f}"
    st_ = vp["state"]
    rows = [
        ("Bar", _stamp(df.index[-1], intraday)),
        ("Surprise (σ)", fmt(s["u"][t], "0.00")),
        ("Landing band · upper (σ)", fmt(s["bU"][t], "0.00")), ("Landing band · lower (σ)", fmt(-s["bD"][t] if not _na(s["bD"][t]) else float("nan"), "0.00")),
        ("Landing band · upper", px(s["upper"][t - H_] if t >= H_ else float("nan"))), ("Landing band · lower", px(s["lower"][t - H_] if t >= H_ else float("nan"))),
        ("Midline", px(s["midL"][t])), ("Cone · upper", px(s["upper"][t])), ("Cone · lower", px(s["lower"][t])),
        ("Stop · long", px(s["stopL"][t])), ("Stop · short", px(s["stopS"][t])),
        ("Risk per bar (σ, log)", fmt(s["sig"][t], "0.0000")), ("Risk rank (500 bars)", fmt(s["prk"][t], "0.0")),
        ("Risk momentum (log)", fmt(s["rMom"][t], "+0.000;-0.000")), ("Trend (σ)", fmt(s["T"][t], "+0.00;-0.00")),
        ("Ladder position", fmt(s["ladX"][t], "+0.00;-0.00")), ("Exposure", f_pct(s["E"][t], "#")),
        ("Profile · POC", px(st_["poc"])), ("Profile · VAH", px(st_["vah"])), ("Profile · VAL", px(st_["val"])),
        ("Profile · VWAP", px(st_["vwap"])), ("Profile · row size", px(st_["binw"])),
    ]
    with K.panel("datawindow", "Data window", context="every plotted value on the last bar"):
        K.kv_list([(k, H.escape(v)) for k, v in rows], cls="kv two-col")
