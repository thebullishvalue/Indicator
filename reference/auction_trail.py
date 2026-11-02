"""Pragati v9.6 - auction engine and Acceptance Trail: Python reference (spec v2).

Implements docs/auction-trail-spec.md sections 2-4 exactly, so the audit port
can be checked bar for bar against pragati.pine (section "AUCTION ENGINE ·
ACCEPTANCE TRAIL"). Two inputs come from the rest of Pragati, as the spec
defines them:

  weight  the conviction engine's participation weight w (f_convCore):
          participation() below computes it from OHLCV for each mode - a
          convenience; for strict parity pass your port's own w (seeding of
          the EMAs differs only inside warm-up, which the trail never reads)
  push    the Conviction-Value Grid's push gate gGate (+1 / 0 / -1); pass the
          series your port computes

    from auction_trail import participation, auction_trail
    w   = participation(high, low, close, volume)            # 'Auto', 20, cap 3
    out = auction_trail(high, low, close, w, push, n=20, mintick=0.01)

Returns a dict of lists, one value per bar: val, poc, vah, mig, dir, lvl,
probe, onset (a probe's first bar), flip. Undefined values are None.
"""
from __future__ import annotations

import math
from typing import Optional, Sequence


def _rma(x, length):
    """ta.rma: seeded with the SMA of the first `length` values."""
    out, seed, s = [], [], None
    for v in x:
        if s is None:
            seed.append(v)
            if len(seed) == length:
                s = sum(seed) / length
        else:
            s = (s * (length - 1) + v) / length
        out.append(s)
    return out


def _ema(x, length):
    """ta.ema: seeded with the SMA of the first `length` non-None values."""
    a, out, seed, s = 2.0 / (length + 1), [], [], None
    for v in x:
        if s is None:
            if v is not None:
                seed.append(v)
                if len(seed) == length:
                    s = sum(seed) / length
        elif v is not None:
            s = a * v + (1 - a) * s
        out.append(s)
    return out


def _true_range(high, low, close):
    return [high[0] - low[0]] + [max(high[i], close[i - 1]) - min(low[i], close[i - 1]) for i in range(1, len(close))]


def _atr_wilder(high, low, close, length=20):
    """ta.atr(length) = ta.rma(ta.tr(true), length)."""
    return _rma(_true_range(high, low, close), length)


def participation(high, low, close, volume, mode="Auto", n=20, cap=3.0):
    """f_convCore's weight w, line for line: volume relative to its EMA (the last
    good print carried through hollow bars), relative true range where there is
    no print, capped. mode: 'Auto', 'Volume', 'True range' or 'Off'."""
    tr = _true_range(high, low, close)
    last, carried = None, []
    for v in volume:
        if v is not None and v > 0:
            last = v
        carried.append(last)
    va, ta = _ema(carried, n), _ema(tr, n)
    w = []
    for i in range(len(close)):
        vok = volume[i] is not None and volume[i] > 0
        wv = volume[i] / va[i] if (vok and va[i] is not None and va[i] > 1e-12) else None
        wr = tr[i] / ta[i] if (ta[i] is not None and ta[i] > 1e-12) else 1.0
        wx = 1.0 if mode == "Off" else wr if mode == "True range" else (wv if wv is not None else 1.0) if mode == "Volume" else (wv if wv is not None else wr)
        w.append(min(max(wx if wx is not None else 1.0, 0.0), cap))
    return w


def _profile(high, low, weight, t, n, atr, mintick):
    """Spec section 3 for the window ending at bar t. Returns (val, poc, vah)."""
    lo = min(low[t - n + 1:t + 1])
    hi = max(high[t - n + 1:t + 1])
    # an absolute grid: a power of two of the tick, nearest ATR(20)/4
    # Pine's math.round takes ties up; Python's round() takes them to even
    bw = mintick * 2.0 ** math.floor(math.log(max(atr / 4.0, mintick) / mintick) / math.log(2.0) + 0.5)
    k_lo = math.floor(lo / bw)
    nb = math.floor(hi / bw) - k_lo + 1
    while nb > 300:
        bw *= 2.0
        k_lo = math.floor(lo / bw)
        nb = math.floor(hi / bw) - k_lo + 1
    base = k_lo * bw
    vb = [0.0] * nb
    tot = 0.0
    for i in range(t - n + 1, t + 1):
        v = weight[i] or 0.0
        if v > 0.0:
            ka = max(0, min(nb - 1, math.floor(low[i] / bw) - k_lo))
            kb = max(0, min(nb - 1, math.floor(high[i] / bw) - k_lo))
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
    return base + kl * bw, base + (kp + 0.5) * bw, base + (kh + 1) * bw


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
                  weight: Sequence[Optional[float]], push: Sequence[Optional[float]],
                  n: int = 20, mintick: float = 0.01) -> dict:
    m = len(close)
    atr = _atr_wilder(high, low, close, 20)
    out = {k: [None] * m for k in ("val", "poc", "vah", "mig")}
    out.update({"dir": [0] * m, "lvl": [None] * m, "probe": [False] * m, "onset": [False] * m, "flip": [False] * m})
    d, lvl, prev_probe = 0, None, False
    for t in range(m):
        if t >= n - 1:
            a = atr[t] if atr[t] is not None else mintick
            val, poc, vah = _profile(high, low, weight, t, n, max(a, mintick), mintick)
        else:
            val = poc = vah = None
        out["val"][t], out["poc"][t], out["vah"][t] = val, poc, vah
        pv = out["val"][t - n] if t - n >= 0 else None
        ph = out["vah"][t - n] if t - n >= 0 else None
        mg = _mig(val, poc, vah, pv, ph)
        out["mig"][t] = mg
        probe = False
        # spec section 4.2, on a closed bar - each rule a boolean, as the Pine
        if mg is not None and poc is not None:
            pu = push[t] if push[t] is not None else 0.0
            c = close[t]
            up_in = d == 0 and mg >= 1 and pu > 0 and c >= val
            dn_in = d == 0 and not up_in and mg <= -1 and pu < 0 and c <= vah
            flip_d = d == 1 and c < lvl and poc < lvl and mg <= -1
            flip_u = d == -1 and c > lvl and poc > lvl and mg >= 1
            probe = (d == 1 and c < lvl and not flip_d) or (d == -1 and c > lvl and not flip_u)
            step_u = d == 1 and not flip_d and not probe and mg >= 1 and pu > 0 and val > lvl and c >= val
            step_d = d == -1 and not flip_u and not probe and mg <= -1 and pu < 0 and vah < lvl and c <= vah
            nd = 1 if (up_in or flip_u) else -1 if (dn_in or flip_d) else d
            lvl = val if (up_in or step_u) else vah if (dn_in or step_d) else lvl
            out["flip"][t] = flip_u or flip_d
            d = nd
        out["probe"][t] = probe
        out["onset"][t] = probe and not prev_probe
        prev_probe = probe
        out["dir"][t], out["lvl"][t] = d, lvl
    return out
