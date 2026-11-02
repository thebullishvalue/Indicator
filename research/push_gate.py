"""Pragati's push gate gGate, ported for research: sections 1-2 of pragati.pine
(the conviction engine and its scaling) and the Conviction-Value Grid's tiers.

Defaults: Lookback 20, Participation baseline 20, Smoothing 3, Signal 9,
k 0.5, Normalization 200, Agreement denominator, Auto participation, quiet
regime = the raw share's sigma in the bottom fifth of its last 800 values.

This port is faithful in structure. It is not the audit's bar-for-bar port:
EMA seeding and warm-up counting may differ by a bar or two, and that matters
only inside the warm-up the trail never reads. Rolling statistics use running
sums and a sorted window, so 20 years of 380 markets is a matter of minutes.
"""
from __future__ import annotations

import bisect
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reference"))
from auction_trail import _ema, _true_range, participation  # noqa: E402


def _sma(x, n):
    out, s = [], 0.0
    for i, v in enumerate(x):
        s += v
        if i >= n:
            s -= x[i - n]
        out.append(s / n if i >= n - 1 else None)
    return out


def _stdev(x, n):
    """Population standard deviation over the last n values (ta.stdev, biased)."""
    out, s, s2 = [], 0.0, 0.0
    for i, v in enumerate(x):
        s += v
        s2 += v * v
        if i >= n:
            s -= x[i - n]
            s2 -= x[i - n] * x[i - n]
        if i >= n - 1:
            m = s / n
            out.append(math.sqrt(max(s2 / n - m * m, 0.0)))
        else:
            out.append(None)
    return out


def _percentrank(x, n):
    """ta.percentrank: the share of the previous n values that are <= the current one."""
    out, win = [], []
    for i, v in enumerate(x):
        if i >= n and v is not None and None not in (x[i - n],):
            out.append(100.0 * bisect.bisect_right(win, v) / n)
        else:
            out.append(None)
        if v is not None:
            bisect.insort(win, v)
        if i >= n and x[i - n] is not None:
            del win[bisect.bisect_left(win, x[i - n])]
    return out


def push_gate(high, low, close, volume, n=20, smooth=3, signal=9, k=0.5, norm=200):
    """Returns gGate per bar: +1 a push up, -1 a push down, 0 no push, None warming."""
    m = len(close)
    tr = _true_range(high, low, close)
    cv = [0.0] + [((close[i] - close[i - 1]) / tr[i]) if tr[i] > 1e-12 else 0.0 for i in range(1, m)]
    w = participation(high, low, close, volume, n=n)
    num = _sma([a * b for a, b in zip(cv, w)], n)
    den = _sma([abs(a) * b for a, b in zip(cv, w)], n)
    raw = [(100.0 * a / b) if (a is not None and b is not None and b > 1e-12) else 0.0 for a, b in zip(num, den)]
    rsd = _stdev(raw, norm)
    scaled = [100.0 * math.tanh(0.0 if (s is None or s < 1e-9) else r / (3.0 * s)) for r, s in zip(raw, rsd)]
    fast = _ema(scaled, smooth)
    sig = _ema(fast, signal)
    hist = [(f - s) if (f is not None and s is not None) else 0.0 for f, s in zip(fast, sig)]
    hsd = _stdev(hist, norm)
    dcv = [0.0] + [(fast[i] - fast[i - 1]) if (fast[i] is not None and fast[i - 1] is not None) else 0.0 for i in range(1, m)]
    dsd = _stdev(dcv, norm)
    rank = _percentrank(rsd, 4 * norm)
    warm = n + 20 + 2 * norm + smooth + signal
    gate = [None] * m
    for i in range(1, m):
        if i < warm or hsd[i] is None or dsd[i] is None:
            continue
        above = hist[i] >= 0
        expand = hist[i] > hist[i - 1] if above else hist[i] < hist[i - 1]
        with_ = dcv[i] > 0.1 * dsd[i] if above else dcv[i] < -0.1 * dsd[i]
        impulse = abs(hist[i]) >= k * hsd[i]
        tier = 0 if (expand and impulse) else 1 if expand else 2 if with_ else 3
        quiet = rank[i] is not None and rank[i] < 20.0
        gate[i] = (1.0 if above else -1.0) if (tier != 3 and not quiet) else 0.0
    return gate
