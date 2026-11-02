"""Volume-profile fixes V3 and V4 (docs/audit-vp-panel-v9.9.md), ported from pragati.pine
and checked on random inputs.

V3 · a bar's spread: every bin of its range is reachable, at most 200 are written, and
     the volume written equals the bar's volume.
V4 · histogram rows by price: each row spans exactly step bins, a gap in the session
     stays an empty row, volume is conserved, and there are at most 110 rows.

    python -I research/audit/vp_props.py
"""
import math
import random

rng = random.Random(3)
fails = {}


def check(k, ok):
    if not ok:
        fails[k] = fails.get(k, 0) + 1


# V3 · the spread (v9.9) against the v9.8 truncation
trunc_lost = 0
for _ in range(20000):
    nb = rng.choice([rng.randint(1, 200), rng.randint(201, 5000)])
    kl, v = rng.randint(-10000, 10000), rng.uniform(1, 1e6)
    st = math.ceil(nb / 200.0)
    nv = math.ceil(nb / float(st))
    ks = [kl + j * st for j in range(nv)]
    check("V3a at most 200 bins written", nv <= 200)
    check("V3b volume conserved", abs(sum([v / nv] * nv) - v) < 1e-6 * v)
    check("V3c the written bins span the bar's range", ks[0] == kl and kl + nb - 1 - ks[-1] < st)
    check("V3d identical to v9.8 when the bar fits in 200 bins", nb > 200 or (st == 1 and nv == nb))
    if nb > 200:
        trunc_lost += 1
# V4 · rows by price
for _ in range(5000):
    n = rng.randint(1, 600)
    keys, k = [], rng.randint(-5000, 5000)
    for _ in range(n):
        keys.append(k)
        k += 1 if rng.random() > 0.05 else rng.randint(2, 80)     # occasional price gaps
    vols = [rng.uniform(0, 100) for _ in keys]
    k0, span = keys[0], keys[-1] - keys[0] + 1
    step = max(1, math.ceil(span / 110.0))
    nR = math.ceil(span / float(step))
    rv = [0.0] * nR
    for kk, vv in zip(keys, vols):
        rv[(kk - k0) // step] += vv
    check("V4a at most 110 rows", nR <= 110)
    check("V4b volume conserved", abs(sum(rv) - sum(vols)) < 1e-6 * max(1, sum(vols)))
    present = set(keys)
    for r in range(nR):
        lo, hi = k0 + r * step, k0 + (r + 1) * step - 1
        has = any(x in present for x in range(lo, hi + 1))
        check("V4c a row holds volume only if a bin inside its price span traded", has or rv[r] == 0.0)
    check("V4d identical to v9.8 when the session is gap-free and fits in 110 bins", not (span == n and n <= 110) or (step == 1 and nR == n))
for k in ["V3a at most 200 bins written", "V3b volume conserved", "V3c the written bins span the bar's range", "V3d identical to v9.8 when the bar fits in 200 bins",
          "V4a at most 110 rows", "V4b volume conserved", "V4c a row holds volume only if a bin inside its price span traded", "V4d identical to v9.8 when the session is gap-free and fits in 110 bins"]:
    print(("FAIL " + str(fails[k]) if k in fails else "pass") + "  " + k)
print(f"(by design, {trunc_lost} of the 20,000 test bars were wider than 200 bins - the case v9.8 truncated)")
