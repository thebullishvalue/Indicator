"""Section 7 of pramana.pine - the volume profile and market-structure overlay - ported bar for bar.

Sessions are D on intraday charts, W on daily, M above. Row size is ATR(20) / rows-per-ATR, frozen at the
session's first bar. Each bar's volume goes to the rows its intrabars traded in (lower-timeframe data where
it exists for that bar), or is spread evenly over the bar's range. The profile is built only over the stretch
it draws from: the first session that opens within two naked-POC ages and three sessions of the last bar.
The value area is walked outward from the POC on the last bar and at each session's close.

`build()` returns the per-bar VWAP (and trails) plus, for the last bar, the drawing: rows, lines, boxes and tags,
positioned in bar indices and prices exactly as the script positions them.
"""
from __future__ import annotations

import bisect
import math

import numpy as np
import pandas as pd

from .palette import rgba
from .pramana import Inputs, pine_atr

NAN = float("nan")


def anchor_period(index: pd.DatetimeIndex, tf_sec: int) -> np.ndarray:
    """time(vpAnchorTf) as a session key: the day on intraday charts, the week on daily, the month above."""
    if tf_sec < 86400:
        key = index.normalize()
    elif tf_sec < 7 * 86400:
        key = index.to_period("W-SUN").start_time if index.tz is None else index.tz_localize(None).to_period("W-SUN").start_time
    else:
        key = index.to_period("M").start_time if index.tz is None else index.tz_localize(None).to_period("M").start_time
    return np.asarray(pd.DatetimeIndex(key).asi8)


def session_bars(tf_sec: int) -> int:
    anchor = 86400 if tf_sec < 86400 else 604800 if tf_sec < 7 * 86400 else 2678400
    return max(1, int(math.ceil(anchor / max(tf_sec, 1))))


def ltf_seconds(tf_sec: int) -> int | None:
    """The script's intrabar timeframe: the largest standard one at or under a sixteenth of the chart's."""
    if tf_sec <= 60:
        return None
    for s in (86400, 14400, 7200, 3600, 1800, 900, 600, 300, 180, 120):
        if tf_sec >= 16 * s:
            return s
    return 60


def _locate(keys: list[int], k: int) -> tuple[int, bool]:
    i = bisect.bisect_left(keys, k)
    return i, (i < len(keys) and keys[i] == k)


class _Profile:
    def __init__(self):
        self.keys: list[int] = []
        self.vol: list[float] = []
        self.buy: list[float] = []
        self.sell: list[float] = []

    def clear(self):
        self.keys.clear(); self.vol.clear(); self.buy.clear(); self.sell.clear()

    def add_span(self, kl: int, nb: int, v: float, bv: float, sv: float, tot: float, pv: float, pk):
        pos, _ = _locate(self.keys, kl)
        for k in range(kl, kl + nb):
            nv = v
            if pos < len(self.keys) and self.keys[pos] == k:
                nv = self.vol[pos] + v
                self.vol[pos] = nv
                self.buy[pos] += bv
                self.sell[pos] += sv
            else:
                self.keys.insert(pos, k); self.vol.insert(pos, v); self.buy.insert(pos, bv); self.sell.insert(pos, sv)
            tot += v
            if nv > pv:
                pv, pk = nv, k
            pos += 1
        return tot, pv, pk

    def walk(self, tot: float, key, binw: float, va_pct: float, poc0, vah0, val0):
        n = len(self.keys)
        if n > 0 and key is not None and binw is not None and not math.isnan(binw):
            pi, found = _locate(self.keys, key)
            if found:
                target = tot * va_pct
                lo = hi = pi
                acc = self.vol[pi]
                guard = 0
                while acc < target and (lo > 0 or hi < n - 1) and guard < n + 2:
                    guard += 1
                    vd = self.vol[lo - 1] if lo > 0 else -1.0
                    vu = self.vol[hi + 1] if hi < n - 1 else -1.0
                    if vu >= vd:
                        hi += 1; acc += vu
                    else:
                        lo -= 1; acc += vd
                return (key + 0.5) * binw, (self.keys[hi] + 1.0) * binw, self.keys[lo] * binw
        return poc0, vah0, val0


def build(d: pd.DataFrame, inp: Inputs, tf_sec: int, mintick: float, pal: dict, intrabars: dict | None = None,
          cone_on: bool = False) -> dict:
    """d: the chart's bars (open/high/low/close/volume). intrabars: {bar position: DataFrame of its lower-timeframe bars}.

    Returns {"vwap": array, "trail": {...}, "draw": {...}, "state": {...}}.
    """
    o, h, l, c = (d[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    vol = d["volume"].to_numpy(float) if "volume" in d else np.full(len(c), NAN)
    n = len(c)
    last = n - 1
    is_intra = tf_sec < 86400
    chart_on = inp.vp
    ctx_on = chart_on and (inp.vp_histogram or inp.vp_va or inp.vp_poc or inp.vp_trail or inp.vp_prev or inp.vp_naked)
    hist_on = chart_on and inp.vp_histogram and ctx_on
    va_on = chart_on and inp.vp_va and ctx_on
    poc_on = chart_on and inp.vp_poc and ctx_on
    nodes_on = hist_on and inp.vp_nodes
    naked_on = chart_on and inp.vp_naked and ctx_on
    prev_on = chart_on and inp.vp_prev and ctx_on
    trail_on = chart_on and inp.vp_trail and ctx_on
    vwap_on = chart_on and inp.vp_vwap
    ib_on = chart_on and inp.vp_ib and is_intra
    delta = inp.vp_style != "Monochrome"
    mono = not delta

    has_vol = (~np.isnan(vol)) & (vol != 0.0)
    vol_share = np.cumsum(has_vol) / (np.arange(n) + 1)
    vol_usable = vol_share >= 0.5
    vol_off = (not inp.vp_use_vol) | ~vol_usable
    tpo_auto = inp.vp_use_vol and not bool(vol_usable[last]) if n else False

    sess = anchor_period(d.index, tf_sec)
    new_sess = np.r_[True, sess[1:] != sess[:-1]]
    atr = np.maximum(np.nan_to_num(pine_atr(h, l, c, 20), nan=mintick), mintick)

    reach = 2 * inp.vp_naked_age + 3 * session_bars(tf_sec)
    intra_use = ctx_on and inp.vp_intrabar and tf_sec > 60 and intrabars is not None

    prof = _Profile()
    binw = NAN
    tot, pk, pv = 0.0, None, 0.0
    poc = vah = val = NAN
    prev_poc = prev_vah = prev_val = NAN
    intra_ok = False
    live = False
    used_intrabar_bars = 0
    trail_poc = np.full(n, NAN); trail_vah = np.full(n, NAN); trail_val = np.full(n, NAN)
    np_y: list[float] = []
    np_x: list[int] = []
    sess_pv = sess_vv = 0.0
    ibh = ibl = NAN
    sess_start = None
    vwap = np.full(n, NAN)

    pc = np.r_[NAN, c[:-1]]
    for t in range(n):
        if not live and new_sess[t] and (inp.vp_trail or t >= last - reach):
            live = True
        if ctx_on and live:
            if new_sess[t]:
                if not inp.vp_trail:
                    poc, vah, val = prof.walk(tot, pk, binw, inp.vp_va_pct, poc, vah, val)
                prev_poc, prev_vah, prev_val = poc, vah, val
                prof.clear()
                tot, pk, pv = 0.0, None, 0.0
                binw = (max(mintick, inp.vp_bin_ticks * mintick) if inp.vp_bin_mode == "Fixed ticks"
                        else max(mintick, atr[t] / inp.vp_bins_per_atr))
            # accumulation (f_vpBuild)
            if not math.isnan(binw) and binw > 0:
                used = False
                ib = intrabars.get(t) if intra_use else None
                if ib is not None and len(ib) > 0:
                    used = True
                    used_intrabar_bars += 1
                    m = len(ib)
                    prevC = pc[t]
                    for ih, il, iv_raw, ic in zip(ib["high"].to_numpy(float), ib["low"].to_numpy(float),
                                                  ib["volume"].to_numpy(float), ib["close"].to_numpy(float)):
                        iv = 1.0 / m if vol_off[t] else max(0.0 if math.isnan(iv_raw) else iv_raw, 0.0)
                        bvn = svn = iv * 0.5
                        if delta and not math.isnan(ic) and not math.isnan(prevC):
                            if ic > prevC:
                                bvn, svn = iv, 0.0
                            elif ic < prevC:
                                bvn, svn = 0.0, iv
                        if not math.isnan(ic):
                            prevC = ic
                        if not math.isnan(ih) and not math.isnan(il):
                            kl = int(math.floor(il / binw)); kh = int(math.floor(ih / binw))
                            nb = max(1, min(kh - kl + 1, 200))
                            tot, pv, pk = prof.add_span(kl, nb, iv / nb, bvn / nb, svn / nb, tot, pv, pk)
                if not used:
                    trHi = max(h[t], h[t] if math.isnan(pc[t]) else pc[t])
                    trLo = min(l[t], l[t] if math.isnan(pc[t]) else pc[t])
                    rng = max(trHi - trLo, mintick)
                    share = min(1.0, max(0.0, (c[t] - trLo) / rng)) if delta else 0.5
                    bv_ = 1.0 if vol_off[t] else max(0.0 if math.isnan(vol[t]) else vol[t], 0.0)
                    kl = int(math.floor(l[t] / binw)); kh = int(math.floor(h[t] / binw))
                    nb = max(1, min(kh - kl + 1, 200))
                    tot, pv, pk = prof.add_span(kl, nb, bv_ / nb, bv_ * share / nb, (bv_ - bv_ * share) / nb, tot, pv, pk)
                intra_ok = used
            if inp.vp_trail or t == last:
                poc, vah, val = prof.walk(tot, pk, binw, inp.vp_va_pct, poc, vah, val)
            if trail_on and not new_sess[t]:
                trail_poc[t], trail_vah[t], trail_val[t] = poc, vah, val

        # naked POC ledger
        if np_y:
            for kn in range(len(np_y) - 1, -1, -1):
                if h[t] >= np_y[kn] and l[t] <= np_y[kn]:
                    np_y.pop(kn); np_x.pop(kn)
        if ctx_on and live and new_sess[t] and not math.isnan(prev_poc):
            if not any(abs(y - prev_poc) <= atr[t] * 0.1 for y in np_y):
                np_y.append(prev_poc); np_x.append(t)
                while len(np_y) > inp.vp_naked_max:
                    np_y.pop(0); np_x.pop(0)
        while np_x and t - np_x[0] > inp.vp_naked_age:
            np_y.pop(0); np_x.pop(0)

        # session VWAP and Initial Balance
        if chart_on:
            if new_sess[t]:
                sess_pv = sess_vv = 0.0
                ibh, ibl = h[t], l[t]
                sess_start = t
            wV = 1.0 if vol_off[t] else max(0.0 if math.isnan(vol[t]) else vol[t], 1e-10)
            sess_pv += (h[t] + l[t] + c[t]) / 3.0 * wV
            sess_vv += wV
            if t - (sess_start if sess_start is not None else t) < inp.vp_ib_bars:
                ibh = max(h[t] if math.isnan(ibh) else ibh, h[t])
                ibl = min(l[t] if math.isnan(ibl) else ibl, l[t])
            vwap[t] = sess_pv / sess_vv if sess_vv > 0 else NAN

    state = dict(poc=poc, vah=vah, val=val, prev_poc=prev_poc, prev_vah=prev_vah, prev_val=prev_val, vwap=vwap[last] if n else NAN,
                 ibh=ibh, ibl=ibl, sess_start=sess_start, binw=binw, nrows=len(prof.keys), intrabar_bars=used_intrabar_bars,
                 intra_ok=intra_ok, tpo=bool(vol_off[last]) if n else True, tpo_auto=tpo_auto, naked=list(zip(np_y, np_x)),
                 atr=float(atr[last]) if n else NAN, decimals=max(0, int(round(-math.log10(mintick)))) if mintick > 0 else 2)
    draw = _render(prof, state, inp, pal, last, cone_on, hist_on, va_on, poc_on, nodes_on, naked_on, prev_on, vwap_on, ib_on,
                   mono, pv, pk) if n else {}
    return dict(vwap=vwap if vwap_on else np.full(n, NAN), trail=dict(poc=trail_poc, vah=trail_vah, val=trail_val),
                new_sess=new_sess, draw=draw, state=state)


def _render(prof, s, inp, pal, bar, cone_on, hist_on, va_on, poc_on, nodes_on, naked_on, prev_on, vwap_on, ib_on, mono, pocVol, pocKey):
    """f_vpRender and f_vpLevels on the last bar: boxes, lines and tags in bar-index and price coordinates."""
    VP_GUTTER, VP_XBACK, VP_OFFSET = 1, 5000, 1
    VP_CONE = min(inp.H, 10) if cone_on else 0
    left = bar + 3 + VP_OFFSET
    right = left + inp.vp_width
    binw = s["binw"]
    boxes, lines, tags = [], [], []
    tx = (right if hist_on else bar + VP_CONE) + VP_GUTTER

    if hist_on and binw and not math.isnan(binw) and binw > 0 and pocVol > 0:
        max_right = left
        nB = len(prof.keys)
        if nB > 0:
            ROWS_MAX = 110
            step = max(1, int(math.ceil(nB / ROWS_MAX)))
            nR = int(math.ceil(nB / step))
            rV, rB, rS, rLo, rHi = [0.0] * nR, [0.0] * nR, [0.0] * nR, [0.0] * nR, [0.0] * nR
            rP = [False] * nR
            pIdx, pFound = _locate(prof.keys, pocKey) if pocKey is not None else (-1, False)
            for i in range(nB):
                rr = i // step
                rV[rr] += prof.vol[i]; rB[rr] += prof.buy[i]; rS[rr] += prof.sell[i]
                if i % step == 0:
                    rLo[rr] = prof.keys[i] * binw
                if i % step == step - 1 or i == nB - 1:
                    rHi[rr] = (prof.keys[i] + 1.0) * binw
                if pFound and i == pIdx:
                    rP[rr] = True
            rMax = max(rV) if rV else 0.0
            pos = [v for v in rV if v > 0]
            hvMean = sum(pos) / len(pos) if pos else 0.0
            hvSd = math.sqrt(sum((v - hvMean) ** 2 for v in pos) / len(pos)) if pos else 0.0
            hvnTh = hvMean + 1.2 * hvSd
            lvnTh = hvMean - 0.6 * hvSd
            srt = sorted(pos)
            if len(srt) > 10:
                lvnTh = srt[max(0, int(math.floor(len(srt) * 0.10)))]
            for r in range(nR):
                if len(boxes) >= 470:
                    break
                tV = rV[r]
                wTot = max(1, int(round(inp.vp_width * tV / rMax))) if tV > 0 and rMax > 0 else 0
                if wTot <= 0:
                    continue
                yB = rLo[r]; ySpan = rHi[r] - yB; yT = yB + ySpan * 0.85; pcm = yB + ySpan / 2.0
                isPoc = rP[r]
                max_right = max(max_right, left + wTot)
                inVa = not math.isnan(s["vah"]) and not math.isnan(s["val"]) and s["val"] <= pcm <= s["vah"]
                fade = 48 if inVa else 72
                if mono:
                    col = pal["POC"] if isPoc else pal["VA"] if inVa else pal["NODE"]
                    boxes.append(dict(x1=left, x2=left + wTot, y1=yT, y2=yB, fill=rgba(col, 25 if isPoc else fade), kind="row"))
                else:
                    wB = int(round(wTot * rB[r] / tV)) if tV > 0 else 0
                    if wB > 0:
                        boxes.append(dict(x1=left, x2=left + wB, y1=yT, y2=yB, fill=rgba(pal["UP"], fade), kind="row"))
                    if wTot - wB > 0:
                        boxes.append(dict(x1=left + wB, x2=left + wTot, y1=yT, y2=yB, fill=rgba(pal["DN"], fade), kind="row"))
                    if isPoc:
                        boxes.append(dict(x1=left, x2=left + wTot, y1=yT, y2=yB, fill=None, border=rgba(pal["POC"], 0), kind="row"))
                if nodes_on and 0 < r < nR - 1 and not isPoc and tV > 0:
                    vL, vR = rV[r - 1], rV[r + 1]
                    if tV >= hvnTh and tV > vL and tV > vR:
                        boxes.append(dict(x1=left - 2, x2=left - 1, y1=yT, y2=yB, fill=rgba(pal["HVN"], 40), kind="node"))
                    elif tV <= lvnTh and tV < vL and tV < vR:
                        boxes.append(dict(x1=left - 2, x2=left - 1, y1=pcm + binw * 0.08, y2=pcm - binw * 0.08,
                                          fill=rgba(pal["LVN"], 40), kind="node"))
            if max_right > left:
                tx = max_right + VP_GUTTER

    # f_vpLevels: tags first (they claim rows in this order), then lines
    seated: list[float] = []
    min_gap = s["atr"] * 0.60

    def tag(y, txt, col, on):
        if on and y is not None and not math.isnan(y) and all(abs(yy - y) >= min_gap for yy in seated):
            seated.append(y)
            tags.append(dict(x=tx, y=y, text=f"{txt} {_fmt(y, s)}", color=col, bg=rgba(col, 88)))

    tag(s["poc"], "POC", pal["POC"], poc_on)
    tag(s["vah"], "VAH", pal["VA"], va_on)
    tag(s["val"], "VAL", pal["VA"], va_on)
    tag(s["vwap"], "VWAP", pal["VWAP"], vwap_on)
    tag(s["ibh"], "IBH", pal["VIOLET"], ib_on)
    tag(s["ibl"], "IBL", pal["VIOLET"], ib_on)
    x_sess = max(max(s["sess_start"] if s["sess_start"] is not None else 0, bar - VP_XBACK), 0)
    if poc_on and not math.isnan(s["poc"]):
        lines.append(dict(x1=x_sess, x2=tx, y=s["poc"], color=rgba(pal["POC"], 0), width=2, style="solid"))
    if va_on and not math.isnan(s["vah"]) and not math.isnan(s["val"]):
        boxes.insert(0, dict(x1=x_sess, x2=bar, y1=s["vah"], y2=s["val"], fill=rgba(pal["VA"], 93), kind="va"))
        lines.append(dict(x1=x_sess, x2=tx, y=s["vah"], color=rgba(pal["VA"], 20), width=1, style="solid"))
        lines.append(dict(x1=x_sess, x2=tx, y=s["val"], color=rgba(pal["VA"], 20), width=1, style="solid"))
    if vwap_on and not math.isnan(s["vwap"]):
        lines.append(dict(x1=bar, x2=tx, y=s["vwap"], color=rgba(pal["VWAP"], 45), width=1, style="solid"))
    if ib_on and not math.isnan(s["ibh"]):
        lines.append(dict(x1=x_sess, x2=tx, y=s["ibh"], color=rgba(pal["VIOLET"], 20), width=1, style="dashed"))
        lines.append(dict(x1=x_sess, x2=tx, y=s["ibl"], color=rgba(pal["VIOLET"], 20), width=1, style="dashed"))
    if prev_on and not math.isnan(s["prev_poc"]):
        lines.append(dict(x1=x_sess, x2=tx, y=s["prev_poc"], color=rgba(pal["POC"], 55), width=1, style="dotted"))
        lines.append(dict(x1=x_sess, x2=tx, y=s["prev_vah"], color=rgba(pal["VA"], 55), width=1, style="dotted"))
        lines.append(dict(x1=x_sess, x2=tx, y=s["prev_val"], color=rgba(pal["VA"], 55), width=1, style="dotted"))
        tag(s["prev_poc"], "pPOC", pal["POC"], prev_on)
        tag(s["prev_vah"], "pVAH", pal["VA"], prev_on)
        tag(s["prev_val"], "pVAL", pal["VA"], prev_on)
    if naked_on and s["naked"]:
        x_min = max(0, bar - min(inp.vp_naked_age, VP_XBACK))
        for ny, nx in s["naked"]:
            if not (prev_on and ny == s["prev_poc"]):
                lines.append(dict(x1=max(x_min, nx), x2=bar, y=ny, color=rgba(pal["POC"], 30), width=1, style="dotted"))
    return dict(boxes=boxes, lines=lines, tags=tags, tag_x=tx, left=left, right=right)


def _fmt(y: float, s: dict) -> str:
    return f"{y:,.{s.get('decimals', 2)}f}"
