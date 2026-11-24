"""The chart: Anumaan drawn on TradingView's open-source Lightweight Charts library (Apache-2.0).

`payload()` turns the engine's output into what the chart draws - every plot, colour, marker and drawing of
anumaan.pine, in its own z-order - and `html()` returns the self-contained component. Drawings the library has no
series for (profile rows, level lines and their tags, the forward cone, the tapes' labels) are custom primitives
positioned in bar indices and prices, exactly as the script positions them.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from engine.palette import (A_FAINT, A_FIRM, A_QUIET, A_SOLID, A_WARM, from_gradient, rgba)
from engine.table import words

STATIC = Path(__file__).parent / "static"
CLIP, TAPE_Y, TAPE_H, OUT_Y, OUT_H = 3.5, 4.3, 0.40, 5.15, 0.22


def _num(x):
    return None if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))) else float(x)


def _times(index: pd.DatetimeIndex) -> list[int]:
    """Bar times as the chart shows them: the exchange's wall clock, encoded as UTC seconds."""
    if index.tz is not None:
        local = index.tz_localize(None)
    else:
        local = index
    return (local.asi8 // 10 ** 9).astype(int).tolist()


def payload(df: pd.DataFrame, e: dict, vp: dict, meta: dict, pal: dict, dark: bool, tokens: dict, tf_sec: int,
            decimals: int, mintick: float, show_volume: bool = True, table_rows: list | None = None) -> dict:
    s, inp = e["series"], e["inputs"]
    n = len(df)
    H = inp.H
    times = _times(df.index)
    step = tf_sec if tf_sec < 86400 else 86400 * (1 if tf_sec < 604800 else 7 if tf_sec < 2600000 else 30)
    future = [times[-1] + step * k for k in range(1, 80)] if n else []
    o, h, l, c, v = (df[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
    vSur, vPrf = inp.pane == "Surprise", inp.pane == "Proof"

    vols = [dict(time=times[i], value=_num(v[i]) or 0.0, color=(tokens["vol_up"] if c[i] >= o[i] else tokens["vol_down"])) for i in range(n)]

    def line(arr, on=True, shift=0):
        out = []
        for i in range(n):
            j = i - shift
            val = _num(arr[j]) if (on and 0 <= j < n) else None
            out.append(dict(time=times[i], value=val) if val is not None else dict(time=times[i]))
        return out

    # ── 8 · THE PANE: columns, band, tapes ────────────────────────────────────
    u, T, trRaw, settled, mU, mD = s["u"], s["T"], s["trRaw"], s["settled"], s["mU"], s["mD"]
    cols, bandU, bandD = [], [], []
    tT, tL, tR, tM = [], [], [], []
    for i in range(n):
        ui = u[i]
        with_ = (not math.isnan(ui)) and ((ui >= 0 and trRaw[i] == 2) or (ui < 0 and trRaw[i] == 0))
        hue = (pal["UP"] if ui >= 0 else pal["DN"]) if with_ else pal["NEUT"]
        if not settled[i]:
            col = rgba(pal["NEUT"], A_WARM)
        elif mU[i] or mD[i]:
            col = rgba(hue if with_ else pal["TEXT"], A_SOLID)
        else:
            col = rgba(hue, A_QUIET if with_ else A_FAINT)
        if vSur and not math.isnan(ui):
            cols.append(dict(time=times[i], value=max(-CLIP, min(CLIP, ui)), color=col))
        else:
            cols.append(dict(time=times[i]))
        bu, bd = s["bU"][i], s["bD"][i]
        bandU.append(dict(time=times[i], value=min(bu, CLIP)) if vSur and not math.isnan(bu) else dict(time=times[i]))
        bandD.append(dict(time=times[i], value=max(-bd, -CLIP)) if vSur and not math.isnan(bd) else dict(time=times[i]))
        # tapes
        Ti = T[i]; tAbs = abs(Ti) if not math.isnan(Ti) else NAN_; tHue = pal["UPD"] if (not math.isnan(Ti) and Ti >= 0) else pal["DND"]
        if math.isnan(Ti):
            ct = rgba(pal["NEUT"], A_WARM)
        elif tAbs < 0.5:
            ct = from_gradient(tAbs, 0.0, 0.5, (tHue, A_WARM), (tHue, A_QUIET))
        else:
            ct = from_gradient(tAbs, 0.5, 1.5, (tHue, 30), (tHue, A_SOLID))
        lx = s["ladX"][i]; lHue = pal["UP"] if (not math.isnan(lx) and lx >= 0) else pal["DN"]; lN = s["ladN"][i]
        if not s["ladOk"][i]:
            cl = rgba(pal["NEUT"], A_WARM)
        elif lN >= 3:
            cl = rgba(lHue, A_SOLID)
        elif lN >= 1:
            cl = rgba(lHue, 72)
        else:
            cl = from_gradient(abs(lx), 0.0, 1.0, (lHue, A_WARM), (lHue, 82))
        prk, rr = s["prk"][i], s["regRaw"][i]
        if not s["regOk"][i]:
            cr = rgba(pal["NEUT"], A_WARM)
        elif rr == 2:
            cr = from_gradient(prk, 200 / 3, 100.0, (pal["GOLD"], A_FIRM), (pal["GOLD"], A_SOLID))
        elif rr == 1:
            cr = from_gradient(prk, 100 / 3, 200 / 3, (pal["GOLD"], A_QUIET), (pal["GOLD"], 55))
        else:
            cr = from_gradient(prk, 0.0, 100 / 3, (pal["GOLD"], 95), (pal["GOLD"], 86))
        rm, rs = s["rMom"][i], s["rmS"][i]
        if math.isnan(rm):
            cm = rgba(pal["NEUT"], A_WARM)
        elif rs == 2:
            cm = from_gradient(abs(rm), 0.10, 0.40, (pal["GOLD"], A_QUIET), (pal["GOLD"], A_FIRM))
        elif rs == 0:
            cm = from_gradient(abs(rm), 0.10, 0.40, (pal["NEUT"], A_QUIET), (pal["NEUT"], 50))
        else:
            cm = rgba(pal["NEUT"], A_FAINT)
        on = vSur and inp.tapes
        tT.append(dict(time=times[i], value=TAPE_Y + TAPE_H, color=ct) if on else dict(time=times[i]))
        tL.append(dict(time=times[i], value=OUT_Y + OUT_H, color=cl) if on else dict(time=times[i]))
        tR.append(dict(time=times[i], value=-TAPE_Y + TAPE_H, color=cr) if on else dict(time=times[i]))
        tM.append(dict(time=times[i], value=-OUT_Y + OUT_H, color=cm) if on else dict(time=times[i]))

    proofF = [dict(time=times[i], value=100.0 * math.log(s["eqF"][i])) if (vPrf and e["last"]["nP"] > 0) else dict(time=times[i]) for i in range(n)]
    proofH = [dict(time=times[i], value=100.0 * math.log(s["eqH"][i])) if (vPrf and e["last"]["nP"] > 0) else dict(time=times[i]) for i in range(n)]

    # ── on the price chart ───────────────────────────────────────────────────
    landU = line(s["upper"], inp.land, shift=H)
    landD = line(s["lower"], inp.land, shift=H)
    stopLh = line(s["stopL"], inp.trail)
    stopSh = line(s["stopS"], inp.trail)
    midl = line(s["midL"], inp.mid)
    vwap = line(vp["vwap"], inp.vp and inp.vp_vwap)
    trails = {}
    if inp.vp_trail and inp.vp:
        for k in ("vah", "val", "poc"):
            trails[k] = line(vp["trail"][k])

    markers = []
    for i in range(n):
        if inp.mid and inp.mid_marks and s["midUp"][i]:
            markers.append(dict(time=times[i], position="belowBar", shape="circle", color=rgba(pal["UP"], 45), size=0.6))
        if inp.mid and inp.mid_marks and s["midDn"][i]:
            markers.append(dict(time=times[i], position="aboveBar", shape="circle", color=rgba(pal["DN"], 45), size=0.6))
        if inp.marks and s["provenUp"][i]:
            markers.append(dict(time=times[i], position="belowBar", shape="arrowUp", color=rgba(pal["UP"], 45), size=0.6))
        if inp.marks and s["provenDn"][i]:
            markers.append(dict(time=times[i], position="aboveBar", shape="arrowDown", color=rgba(pal["DN"], 45), size=0.6))

    # the forward cone, the stops, the scale anchors
    t = n - 1
    cone = dict(on=False)
    if inp.cone and n and bool(s["coneOk"][t]):
        sig, qU, qD, cl_ = s["sig"][t], s["qU"][t], s["qD"][t], c[t]
        segs = []
        for i in range(1, H + 1):
            w0, w1 = sig * math.sqrt(i - 1), sig * math.sqrt(i)
            segs.append([t + i - 1, cl_ * math.exp(qU * w0), t + i, cl_ * math.exp(qU * w1)])
            segs.append([t + i - 1, cl_ * math.exp(-qD * w0), t + i, cl_ * math.exp(-qD * w1)])
        stopL, stopS = s["stopL"][t], s["stopS"][t]
        topY, botY = max(stopS, s["upper"][t]), min(stopL, s["lower"][t])
        vc = min(H, 10)
        cone = dict(on=True, segs=segs, color=rgba(pal["CONE"], 55), stopL=stopL, stopS=stopS, x0=t, x1=t + H,
                    stopLc=rgba(pal["DN"], 50), stopSc=rgba(pal["UP"], 50), topY=topY, botY=botY, tagX=t + vc,
                    tagC=rgba(pal["CONE"], 25), topTxt=f"short stop {stopS:.{decimals}f}", botTxt=f"long stop {stopL:.{decimals}f}")

    W = words(e, t) if n else {}
    tape_tags = []
    if vSur and inp.tapes and n:
        tInk = pal["UP"] if trRaw[t] == 2 and not math.isnan(T[t]) else pal["DN"] if trRaw[t] == 0 and not math.isnan(T[t]) else pal["NEUT"]
        tape_tags = [dict(x=t + 1, y=(TAPE_Y + OUT_Y) / 2.0, text=f"LADDER {W['ladShort']}\nTREND {W['trWord']}", color=tInk),
                     dict(x=t + 1, y=-(TAPE_Y + OUT_Y) / 2.0, text=f"RISK {W['regTxt']}\nMOMENTUM {W['rmWord']}",
                          color=pal["GOLD"] if (s["regRaw"][t] == 2 or s["rmS"][t] == 2) else pal["NEUT"])]

    status_col = cols[-1].get("color", rgba(pal["NEUT"], A_WARM)) if cols else None
    colours: dict[str, int] = {}

    def pack(objs):
        """[{time, value, color?}] -> {"v": [...], "c": [...]} with colours as indices into one shared list."""
        v = [o.get("value") for o in objs]
        if any("color" in o for o in objs):
            c_ = [colours.setdefault(o["color"], len(colours)) if "color" in o else None for o in objs]
            return dict(v=v, c=c_)
        return dict(v=v)
    status = dict(value=_num(u[t]) if n else None, color=status_col)
    packed = {k: pack(x) for k, x in dict(cols=cols, bandU=bandU, bandD=bandD, tT=tT, tL=tL, tR=tR, tM=tM, proofF=proofF, proofH=proofH,
                                         landU=landU, landD=landD, stopLh=stopLh, stopSh=stopSh, midl=midl, vwap=vwap).items()}
    packed["trails"] = {k: pack(x) for k, x in trails.items()}
    packed["vols"] = pack(vols)
    return dict(
        times=times, o=o.tolist(), h=h.tolist(), l=l.tolist(), c=c.tolist(), future=future, showVolume=show_volume,
        decimals=decimals, mintick=mintick, intraday=tf_sec < 86400, pane=inp.pane, tapes=vSur and inp.tapes,
        tapeBase=dict(tT=TAPE_Y - TAPE_H, tL=OUT_Y - OUT_H, tR=-TAPE_Y - TAPE_H, tM=-OUT_Y - OUT_H), markers=markers,
        landColor=rgba(pal["CONE"], 80), midColor=rgba(pal["CONE"], 50), stopLhColor=rgba(pal["DN"], 50), stopShColor=rgba(pal["UP"], 50),
        vwapColor=rgba(pal["VWAP"], 0), trailVA=rgba(pal["VA"], 75), trailPOC=rgba(pal["POC"], 65),
        bandColor=rgba(pal["CONE"], 40), zeroColor=rgba(pal["NEUT"], 55), proofFColor=rgba(pal["TEXT"], 0), proofHColor=rgba(pal["NEUT"], 20),
        profile=vp["draw"] if inp.vp else dict(boxes=[], lines=[], tags=[]), cone=cone, tapeTags=tape_tags, status=status,
        table=table_rows or [], tablePos=inp.table_pos, tableOn=inp.table, uRaw=[_num(x) for x in u],
        colours=list(colours), **packed,
    )


NAN_ = float("nan")


def html(p: dict, tokens: dict, title: dict, height: int = 760) -> str:
    js = (STATIC / "lightweight-charts.standalone.production.js").read_text(encoding="utf-8")
    app = (STATIC / "chart.js").read_text(encoding="utf-8")
    css = (STATIC / "chart.css").read_text(encoding="utf-8")
    data = json.dumps(_clean(dict(p=p, tokens=tokens, title=title, height=height)), allow_nan=False, default=_json_default)
    root = (f":root{{--axis:{tokens['axis']};--ink:{tokens['ink']};--mono:{tokens['monoFont']};--sans:{tokens['font']};"
            f"--panel:{tokens['panel']};--panel-edge:{tokens['panelEdge']};--accent:{tokens['accent']};"
            f"--accent-fill:{tokens['accentFill']};--hover:{tokens['hover']};--menu-bg:{tokens['menuBg']};}}"
            f" body{{background:{tokens['bg']};}}")
    fonts = ("<link rel='preconnect' href='https://fonts.googleapis.com'><link rel='stylesheet' "
             "href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap'>")
    return (f"<!doctype html><html><head><meta charset='utf-8'>{fonts}<style>{root}{css}</style></head><body>"
            f"<div id='wrap'><div id='chart'></div></div>"
            f"<script>{js}</script><script>window.ANUMAAN={data};</script><script>{app}</script></body></html>")


def _clean(o):
    """NaN and infinities become null, recursively - JSON has no NaN."""
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return None if (math.isnan(o) or math.isinf(o)) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if (math.isnan(o) or math.isinf(o)) else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    raise TypeError(type(o))


def tokens(dark: bool) -> dict:
    """The chart's colours: the design system's Graphite / Paper surfaces, with TradingView's candle colours."""
    if dark:
        return dict(bg="#0F1217", grid="rgba(255,255,255,0.045)", axis="#8B95A6", ink="#E6EAF1", border="rgba(255,255,255,0.08)",
                    crosshair="#737D8E", crosshairLabel="#2A303B", separator="#232833", separatorHover="rgba(76,125,240,0.25)",
                    candle_up="#089981", candle_down="#F23645", candleUp="#089981", candleDown="#F23645",
                    vol_up="rgba(8,153,129,0.45)", vol_down="rgba(242,54,69,0.45)", watermark="rgba(230,234,241,0.045)",
                    panel="rgba(13,18,21,0.92)", panelEdge="rgba(255,255,255,0.10)",
                    accent="#4C7DF0", accentFill="rgba(76,125,240,0.14)", hover="rgba(255,255,255,0.06)", menuBg="#161A21",
                    font="Inter, -apple-system, 'Segoe UI', system-ui, sans-serif", monoFont="'JetBrains Mono', ui-monospace, Menlo, monospace")
    return dict(bg="#FFFFFF", grid="rgba(15,23,42,0.055)", axis="#5E6979", ink="#141920", border="rgba(15,23,42,0.12)",
                crosshair="#6B7482", crosshairLabel="#3D4756", separator="#DCE1E8", separatorHover="rgba(43,95,217,0.25)",
                candle_up="#089981", candle_down="#F23645", candleUp="#089981", candleDown="#F23645",
                vol_up="rgba(8,153,129,0.40)", vol_down="rgba(242,54,69,0.40)", watermark="rgba(20,25,32,0.05)",
                panel="rgba(255,255,255,0.94)", panelEdge="rgba(15,23,42,0.12)",
                accent="#2B5FD9", accentFill="rgba(43,95,217,0.10)", hover="rgba(15,23,42,0.05)", menuBg="#FFFFFF",
                font="Inter, -apple-system, 'Segoe UI', system-ui, sans-serif", monoFont="'JetBrains Mono', ui-monospace, Menlo, monospace")
