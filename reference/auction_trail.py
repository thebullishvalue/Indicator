"""Pragati v9.4 - auction engine and Acceptance Trail: Python reference.

Implements docs/auction-trail-spec.md sections 2-4 exactly, so the audit port
can be checked bar for bar against pragati.pine (section "AUCTION ENGINE ·
ACCEPTANCE TRAIL"). The push gate (the Conviction-Value Grid's gGate) is an
INPUT here, as the spec defines it: pass the series your port computes.

    from auction_trail import auction_trail
    out = auction_trail(high, low, close, volume, push, n=20)

Returns a dict of lists, one value per bar: val, poc, vah, mig, dir, lvl,
probe, flip. Undefined values are None.
"""
from __future__ import annotations

import math
from typing import Optional, Sequence


def _atr_wilder(high, low, close, length=20):
    """ta.atr(length): Wilder RMA of true range, seeded with the SMA of the
    first `length` true ranges, as Pine seeds ta.rma."""
    out: list[Optional[float]] = [None] * len(close)
    trs: list[float] = []
    rma: Optional[float] = None
    for i in range(len(close)):
        if i == 0:
            tr = high[0] - low[0]
        else:
            tr = max(high[i], close[i - 1]) - min(low[i], close[i - 1])
        trs.append(tr)
        if rma is None:
            if len(trs) == length:
                rma = sum(trs) / length
        else:
            rma = (rma * (length - 1) + tr) / length
        out[i] = rma
    return out


def _profile(high, low, vol_w, t, n, bw0, mintick):
    """Spec section 3 for the window ending at bar t. Returns (val, poc, vah)."""
    lo = min(low[t - n + 1:t + 1])
    hi = max(high[t - n + 1:t + 1])
    bw = max(bw0, mintick)
    nb = int(math.floor((hi - lo) / bw)) + 1
    if nb > 300:
        bw = (hi - lo) / 299.0
        nb = 300
    vb = [0.0] * nb
    tot = 0.0
    for i in range(t - n + 1, t + 1):
        v = vol_w[i]
        if v > 0.0:
            ka = max(0, min(nb - 1, int(math.floor((low[i] - lo) / bw))))
            kb = max(0, min(nb - 1, int(math.floor((high[i] - lo) / bw))))
            k0, k1 = min(ka, kb), max(ka, kb)
            per = v / (k1 - k0 + 1)
            for k in range(k0, k1 + 1):
                vb[k] += per
            tot += v
    if tot <= 0.0:
        return None, None, None
    mid = (nb - 1) / 2.0
    kp, best = 0, vb[0]
    for k in range(1, nb):
        tol = 1e-9 * max(best, 1e-12)
        if vb[k] > best + tol or (abs(vb[k] - best) <= tol and abs(k - mid) < abs(kp - mid)):
            best, kp = vb[k], k
    tgt = 0.70 * tot
    kl = kh = kp
    acc = vb[kp]
    while acc < tgt and (kl > 0 or kh < nb - 1):
        vd = vb[kl - 1] if kl > 0 else -1.0
        vu = vb[kh + 1] if kh < nb - 1 else -1.0
        if vu >= vd:
            kh += 1
            acc += vu
        else:
            kl -= 1
            acc += vd
    return lo + kl * bw, lo + (kp + 0.5) * bw, lo + (kh + 1) * bw


def _mig(val, poc, vah, pval, pvah):
    """Spec section 4.1."""
    if None in (val, poc, vah, pval, pvah):
        return None
    if val > pvah:
        return 2
    if vah < pval:
        return -2
    if poc > pvah:
        return 1
    if poc < pval:
        return -1
    return 0


def auction_trail(high: Sequence[float], low: Sequence[float], close: Sequence[float],
                  volume: Sequence[Optional[float]], push: Sequence[Optional[float]],
                  n: int = 20, mintick: float = 0.01) -> dict:
    m = len(close)
    atr = _atr_wilder(high, low, close, 20)
    # usesVolume: expanding share of bars with volume > 0 is at least one half
    seen = 0
    vol_w = [0.0] * m
    uses = [False] * m
    for i in range(m):
        v = volume[i]
        seen += 1 if (v is not None and v > 0) else 0
        uses[i] = seen / (i + 1) >= 0.5
    out = {k: [None] * m for k in ("val", "poc", "vah", "mig")}
    out.update({"dir": [0] * m, "lvl": [None] * m, "probe": [False] * m, "flip": [False] * m})
    d, lvl = 0, None
    for t in range(m):
        # the window's weights follow usesVolume as it stands on bar t
        if t >= n - 1:
            for i in range(t - n + 1, t + 1):
                v = volume[i]
                vol_w[i] = (max(v, 0.0) if v is not None else 0.0) if uses[t] else 1.0
            a = atr[t] if atr[t] is not None else mintick
            val, poc, vah = _profile(high, low, vol_w, t, n, max(a, mintick) / 4.0, mintick)
        else:
            val = poc = vah = None
        out["val"][t], out["poc"][t], out["vah"][t] = val, poc, vah
        pv = out["val"][t - n] if t - n >= 0 else None
        ph = out["vah"][t - n] if t - n >= 0 else None
        mg = _mig(val, poc, vah, pv, ph)
        out["mig"][t] = mg
        # spec section 4.2, on a closed bar
        if mg is not None and poc is not None:
            pu = push[t] if push[t] is not None else 0.0
            c = close[t]
            if d == 0:
                if mg >= 1 and pu > 0 and c >= val:
                    d, lvl = 1, val
                elif mg <= -1 and pu < 0 and c <= vah:
                    d, lvl = -1, vah
            elif d == 1:
                if c < lvl and poc < lvl:
                    d = -1
                    out["flip"][t] = True
                elif c < lvl:
                    out["probe"][t] = True
                elif mg >= 1 and pu > 0 and val > lvl and c >= val:
                    lvl = val
            else:
                if c > lvl and poc > lvl:
                    d = 1
                    out["flip"][t] = True
                elif c > lvl:
                    out["probe"][t] = True
                elif mg <= -1 and pu < 0 and vah < lvl and c <= vah:
                    lvl = vah
        out["dir"][t], out["lvl"][t] = d, lvl
    return out
