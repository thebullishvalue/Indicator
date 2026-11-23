"""Does starting anumaan.pine's volume profile at the gate change the naked-POC list on the last bar?
Replays the Pine bookkeeping bar for bar (bar-range spread, ATR rows frozen at session start, strict POC,
touch removal, de-duplication within 0.1 ATR, cap, age) from the first bar and from the gate, and compares
the lists at many end points."""
import sys, math
import numpy as np
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), ".."))
from lib import load
from multiprocessing import Pool


def tick_of(c):
    return 10.0 ** (math.floor(math.log10(np.nanmedian(c))) - 4)      # about five significant figures


def atr20(h, l, c, TICK):
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.r_[np.nan, c[:-1]]), np.abs(l - np.r_[np.nan, c[:-1]])))
    tr[0] = h[0] - l[0]
    a = np.full(len(c), np.nan)
    if len(c) >= 20:
        a[19] = tr[:20].mean()
        for i in range(20, len(c)):
            a[i] = (a[i - 1] * 19 + tr[i]) / 20
    return np.maximum(np.nan_to_num(a, nan=TICK), TICK)

def replay(h, l, v, atr, new, i0, end, age, maxk, TICK):
    """Bars i0..end with the profile live from i0 (i0 must open a session). Returns the naked list after `end`."""
    keys = {}; pk = None; pv = 0.0; poc = None; binw = None; naked = []
    for i in range(i0, end + 1):
        if new[i]:
            prev = poc
            keys = {}; pk = None; pv = 0.0
            binw = max(TICK, atr[i] / 4)
        else:
            prev = None
        kl = math.floor(l[i] / binw); kh = math.floor(h[i] / binw); nb = max(1, min(kh - kl + 1, 200)); per = v[i] / nb
        for k in range(kl, kl + nb):
            t = keys.get(k, 0.0) + per; keys[k] = t
            if t > pv:
                pv, pk = t, k
        if keys and pk is not None:
            poc = (pk + 0.5) * binw
        naked = [(y, x) for (y, x) in naked if not (h[i] >= y and l[i] <= y)]
        if new[i] and prev is not None:
            if not any(abs(y - prev) <= atr[i] * 0.1 for y, _ in naked):
                naked.append((prev, i))
                while len(naked) > maxk:
                    naked.pop(0)
        while naked and i - naked[0][1] > age:
            naked.pop(0)
    return naked

def one(args):
    sym, d, hourly, age, maxk, mult = args
    h, l, c = d.high.values, d.low.values, d.close.values
    v = np.where(d.volume.values > 0, d.volume.values, 1.0)
    per = d.index.date if hourly else d.index.to_period("W-SUN")
    new = np.r_[True, np.asarray(per[1:] != per[:-1])]
    S = 24 if hourly else 7
    reach = mult * age + 3 * S
    TICK = tick_of(c)
    atr = atr20(h, l, c, TICK)
    n = len(c); diff = tot = 0; nonempty = 0
    for end in range(reach + 50, n, 37):
        full = replay(h, l, v, atr, new, 0, end, age, maxk, TICK)
        i0 = next(i for i in range(max(0, end - reach), end + 1) if new[i])
        gated = replay(h, l, v, atr, new, i0, end, age, maxk, TICK)
        tot += 1; nonempty += bool(full); diff += full != gated
    return sym, tot, nonempty, diff

if __name__ == "__main__":
    for ds, hourly in (("data", False), ("data1h", True)):
        D = load(ds, 2500 if hourly else 1500)
        for age, maxk, mult in ((250, 5, 2), (50, 20, 2), (250, 5, 3), (50, 20, 3)):
            with Pool(4) as p:
                R = p.map(one, [(s, d, hourly, age, maxk, mult) for s, (_c, d) in D.items()])
            T = sum(r[1] for r in R); N = sum(r[2] for r in R); X = sum(r[3] for r in R)
            print(f"{ds} age {age} max {maxk} reach {mult}x age: {T} end points on {len(R)} instruments, {N} with naked POCs, {X} differ",
                  [r[0] for r in R if r[3]][:5], flush=True)
